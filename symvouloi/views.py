import json
from django.contrib.auth.models import Group
import os
import mimetypes
import requests
from datetime import datetime
from django.utils import timezone
import csv
from io import TextIOWrapper

from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import RedirectView, TemplateView

from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import TeacherAssignment, Teacher, EvaluationStep, EvaluationStepType, EvaluationData
from metakinhseis.models import Consultant

from django.contrib import messages
from django.contrib.auth.models import Group
from django.urls import reverse
from django.views.generic import ListView
from unfold.views import UnfoldModelAdminViewMixin
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from metakinhseis.models import Metakinhsh
from django.contrib.admin import site
from django.conf import settings
from django.http import HttpResponseNotFound
from app.utils import is_member


def dashboard_callback(request, context):
    is_elevated = request.user.groups.filter(name='Επόπτες').exists() or request.user.is_superuser
    ekp_cnt = Teacher.objects.all().count() if is_elevated else Teacher.objects.filter(consultant=request.user).count()
    step_cnt = EvaluationStep.objects.all().count() if is_elevated else EvaluationStep.objects.filter(consultant=request.user).count()
    
    teachers = Teacher.objects.filter(is_active=True, participates=True) if is_elevated else \
            Teacher.objects.filter(is_active=True, participates=True, consultant=request.user)
    teachers_meeting_approved = teachers.filter(participates=True, teacher_evaluation_steps__es_type_id=4,
                                                teacher_evaluation_steps__approved=True).count()
    context.update(
        {
            "kpi": [
                {
                    "title": "Εκπαιδευτικοί",
                    "metric": ekp_cnt,
                },
                {
                    "title": "Ενέργειες αξιολόγησης",
                    "metric": step_cnt,
                },
                {
                    "title": "Ολοκληρωμένες αξιολογήσεις",
                    "metric": teachers_meeting_approved,
                },
            ],
        },
    )

    return context



# Get teacher data from Proteas API
# configure API_ENDPOINT & API_KEY @ settings.py
@staff_member_required
def update_teacher_and_consultant(request):
    assignments = TeacherAssignment.objects.all()
    api_endpoint = settings.API_ENDPOINT
    api_key = settings.API_KEY
    nf_teachers = set()
    added_consultants = 0
    added_teachers = 0
    
    # First get all eidikothtes in a dict
    klados_dict = {}
    try:
        full_endpoint = f"{api_endpoint}/klados"
        response = requests.get(full_endpoint, headers={"X-API-Key": api_key})
        response.raise_for_status()
        response_data = response.json().get("records", [])
        klados_dict = {record["id"]: record["perigrafh"] for record in response_data}
    except requests.RequestException as e:
        print(f"Error fetching eidikothtes: {e}")
        return JsonResponse({"status": "Error", "message": "Failed to fetch eidikothtes from API."}, status=500)

    # Then get schools in a dict
    school_dict = {}
    try:
        full_endpoint = f"{api_endpoint}/school"
        response = requests.get(full_endpoint, headers={"X-API-Key": api_key})
        response.raise_for_status()
        response_data = response.json().get("records", [])
        school_dict = {record["id"]: record["name"] for record in response_data}
    except requests.RequestException as e:
        print(f"Error fetching schools: {e}")
        return JsonResponse({"status": "Error", "message": "Failed to fetch schools from API."}, status=500)

    # Proceed to assignments
    for assignment in assignments:
        consultant_afm = assignment.consultant_afm.zfill(9)  # Ensure 9 characters
        teacher_afm = assignment.teacher_afm.zfill(9)

        try:
            # Check if user with consultant_afm exists
            consultant = User.objects.filter(username=consultant_afm).first()
            if not consultant:
                # Fetch data from the API for the consultant. If not found, create without extra data
                try:
                    consultant_full_endpoint = f"{api_endpoint}/employee?filter=afm,eq,{consultant_afm}"
                    response = requests.get(consultant_full_endpoint, headers={"X-API-Key": api_key})
                    response.raise_for_status()
                    consultant_data = response.json().get("records", [])
                    consultant_info = consultant_data[0]
                except:
                    print(f'Consultant with afm {consultant_afm} not found in API. Creating without extra data...')
                    consultant_info = {
                        'email': '',
                        'klados': '',
                        'am': ''
                    }
                # create consultant
                consultant = User.objects.create_user(
                    username=consultant_afm,
                    password=f"{consultant_afm}-pass",
                    first_name=assignment.consultant_first_name,
                    last_name=assignment.consultant_last_name,
                    email=consultant_info.get('email',''),
                    is_staff=True
                )
                added_consultants += 1
                consultant_group = Group.objects.get(name='Σύμβουλοι')
                consultant.groups.add(consultant_group)
                consultant_extra = Consultant.objects.create(
                    user = consultant,
                    klados = klados_dict.get(consultant_info.get("klados", ""), "Unknown"),
                    am = consultant_info.get("am", "")
                )
                print(f'Added consultant {assignment.consultant_last_name}!')
                
            
            # Check if teacher with teacher_afm exists
            teacher = Teacher.objects.filter(afm=teacher_afm).first()
            if not teacher:
                # Fetch data from the API for the teacher
                full_endpoint = f"{api_endpoint}/employee?filter=afm,eq,{teacher_afm}"
                response = requests.get(full_endpoint, headers={"X-API-Key": api_key})
                response.raise_for_status()
                teacher_data = response.json().get("records", [])
                if teacher_data:
                    teacher_info = teacher_data[0]
                    try:
                        is_active = True if teacher_info.get("status", "") == 1 else False
                        teacher = Teacher.objects.create(
                            afm=teacher_info.get("afm", "").zfill(9),
                            evaluation_year=settings.EVALUATION_YEAR,
                            last_name=teacher_info.get("surname", ""),
                            first_name=teacher_info.get("name", ""),
                            father_name=teacher_info.get("patrwnymo", ""),
                            specialty=klados_dict.get(teacher_info.get("klados", ""), "Unknown"),
                            school=school_dict.get(teacher_info.get("sx_yphrethshs", ""), "Unknown"),
                            fek=teacher_info.get('fek_dior', ''),
                            appointment_date=teacher_info.get("hm_dior", None),
                            mobile=teacher_info.get("tel", ""),
                            mail=teacher_info.get("email", ""),
                            participates=True,
                            comments="",
                            is_active=is_active,
                            consultant=consultant
                        )
                        added_teachers += 1
                        print(f'Added teacher {teacher_info["surname"]}')
                        # Update assignment as well
                        assignment.loaded = True
                        assignment.save()
                    except Exception as e:
                        print(f"Error saving teacher {teacher_afm}: {e}")
                        continue
                else:
                    print(f'Teacher {teacher_afm} not found in API. Adding from assignment')
                    teacher = Teacher.objects.create(
                        afm=assignment.teacher_afm,
                        evaluation_year=settings.EVALUATION_YEAR,
                        last_name=assignment.teacher_last_name,
                        first_name=assignment.teacher_first_name,
                        is_active=True,
                        participates=True,
                        consultant=consultant
                    )
                    added_teachers += 1
                    print(f'Teacher {teacher_afm} added from assignment')
                    nf_teachers.add(teacher_afm)
                    assignment.loaded = True
                    assignment.comments = 'Δε βρέθηκε στον Πρωτέα. Προστέθηκε από τον πίνακα αναθέσεων'
                    assignment.save()
                    continue
        except requests.RequestException as e:
            print(f"API call failed for AFM {consultant_afm} or {teacher_afm}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error for assignment {assignment.id}: {e}")
            continue

    print(f'Teachers from assignment table: {len(nf_teachers)}.')
    print(f'List: {list(nf_teachers)}')
    # return JsonResponse({"status": "Success", "message": "Teacher and consultant synchronization completed."})
    return HttpResponse(f"Ο συγχρονισμός εκπ/κών ολοκληρώθηκε. Προστέθηκαν {added_consultants} σύμβουλοι & {added_teachers} εκπ/κοί.")


# Update teachers from API
@staff_member_required
def update_teachers(request):
    api_endpoint = settings.API_ENDPOINT
    api_key = settings.API_KEY
    updated_teachers = 0
    errors = []

    # Get all teachers from the database
    teachers = Teacher.objects.all()

    # Fetch latest teacher data from API
    try:
        full_endpoint = f"{api_endpoint}/employee"
        response = requests.get(full_endpoint, headers={"X-API-Key": api_key})
        response.raise_for_status()
        api_teachers = {t["afm"].zfill(9): t for t in response.json().get("records", [])}  # Normalize AFM
    except requests.RequestException as e:
        return JsonResponse({"status": "Error", "message": f"Σφάλμα ενημέρωσης εκπ/κών από το API: {e}"}, status=500)

    # Fetch school dictionary for `sx_yphrethshs` mapping
    school_dict = {}
    try:
        full_endpoint = f"{api_endpoint}/school"
        response = requests.get(full_endpoint, headers={"X-API-Key": api_key})
        response.raise_for_status()
        school_dict = {record["id"]: record["name"] for record in response.json().get("records", [])}
    except requests.RequestException as e:
        return JsonResponse({"status": "Error", "message": f"Σφάλμα ενημέρωσης σχολείων από το API: {e}"}, status=500)

    # Loop through teachers and compare with API data
    for teacher in teachers:
        afm = teacher.afm.zfill(9)  # Normalize AFM

        if afm in api_teachers:
            api_teacher = api_teachers[afm]
            new_school = school_dict.get(api_teacher.get("sx_yphrethshs", ""), "Άγνωστο")
            new_status = True if api_teacher.get("status", "") == 1 else False

            # Check if any field has changed
            if teacher.school != new_school or teacher.is_active != new_status:
                try:
                    teacher.school = new_school
                    teacher.is_active = new_status
                    teacher.save()
                    updated_teachers += 1
                    print(f"Ενημέρωση εκπ/κού {teacher.last_name} ({afm})")
                except Exception as e:
                    errors.append(f"Σφάλμα ενημέρωσης εκπ/κού {teacher.last_name} ({afm}): {e}")
        else:
            print(f"Ο/Η εκπ/κός {teacher.last_name} ({afm}) δε βρέθηκε στο API.")

    result_message = f"Έγινε ενημέρωση {updated_teachers} εκπ/κών."
    if errors:
        result_message += f" Σφάλματα: {len(errors)}. Ελέγξτε το αρχείο καταγραφής."

    return HttpResponse(result_message)


# Assign multiple users to the selected group
def assign_users_to_group(request):
    user_ids_str = request.GET.get('user_ids', '')
    user_ids = [int(id.strip()) for id in user_ids_str.split(',') if id.strip().isdigit()]
    
    # If the form is submitted
    if request.method == "POST":
        group_name = request.POST.get('group_name')

        if not group_name:
            messages.error(request, "Παρακαλώ δώστε ένα γκρούπ.")
            return redirect(reverse('admin:auth_user_changelist'))  # Redirect back to user list

        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            messages.error(request, f"Η ομάδα '{group_name}' δε βρέθηκε.")
            return redirect(reverse('admin:auth_user_changelist'))  # Redirect back to user list

        # Assign users to the group
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            user.groups.add(group)
            messages.success(request, f"Ο χρήστης {user.username} ανατέθηκε στην ομάδα {group_name}.")
        
        return redirect(reverse('admin:auth_user_changelist'))  # Redirect to the user list page after assignment

    # If it's a GET request, render the form
    groups = Group.objects.all()
    context = {'groups': groups, 'user_ids': user_ids}
    context.update(site.each_context(request))

    return render(request, 'admin/assign_users_to_group.html', context)


# Get evaluation steps in JSON for the FullCalendar view
def evaluation_steps_json(request):
    events = []
    is_consultant = request.user.groups.filter(name='Σύμβουλοι').exists()
    is_elevated = request.user.groups.filter(name='Επόπτες').exists() or request.user.is_superuser
    steps = EvaluationStep.objects.all() if is_elevated else EvaluationStep.objects.filter(consultant=request.user)

    for step in steps:
        if is_consultant:
            description = f'{step.es_type} με {step.teacher.last_name} {step.teacher.first_name}'
        else:
            description = f'{step.es_type} {step.consultant.last_name} {step.consultant.first_name} με {step.teacher.last_name} {step.teacher.first_name}'
        step_url = reverse('admin:symvouloi_evaluationstep_change', args=[step.id])

        events.append({
            'title': f"{step.es_type}: {step.teacher.last_name} {step.teacher.first_name}",
            'start': step.es_date.isoformat(),
            'end': step.es_date.isoformat(),  # Use a different field if it's a range
            'allDay': True,  # Adjust if steps span time,
            'description': description,
            'url': step_url,
            'complete': step.complete
        })
    return JsonResponse(events, safe=False)


# Helper function for evaluation step statistics
def compute_step_statistics(educators, step_type_id):
    current_date = timezone.now().date()

    educators_with_step = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=step_type_id)
    educators_step_completed = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=step_type_id,
                                                teacher_evaluation_steps__complete=True)
    educators_step_incomplete = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=step_type_id,
                                                 teacher_evaluation_steps__complete=False)
    educators_step_overdue = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=step_type_id,
                                              teacher_evaluation_steps__complete=False,
                                              teacher_evaluation_steps__es_date__lt=current_date)

    educators_with_step_count = educators_with_step.count()
    educators_step_completed_count = educators_step_completed.count()
    educators_step_incomplete_count = educators_step_incomplete.count()
    educators_step_overdue_count = educators_step_overdue.count()

    return [educators_with_step_count, educators_step_incomplete_count, educators_step_overdue_count, educators_step_completed_count]


def compute_final_evaluation_statistics(educators):
    educators_with_final_eval = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=4)
    educators_pending_final_eval = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=4,
                                                    teacher_evaluation_steps__complete=True,
                                                    teacher_evaluation_steps__to_review=False,
                                                    teacher_evaluation_steps__approved=False)
    educators_incomplete_final_eval = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=4,
                                                       teacher_evaluation_steps__complete=False)
    educators_to_review_final_eval = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=4,
                                                      teacher_evaluation_steps__to_review=True)
    educators_approved_final_eval = educators.filter(participates=True, teacher_evaluation_steps__es_type_id=4,
                                                     teacher_evaluation_steps__approved=True)

    final_eval_count = educators_with_final_eval.count()
    pending_final_eval_count = educators_pending_final_eval.count()
    incomplete_final_eval_count = educators_incomplete_final_eval.count()
    to_review_final_eval_count = educators_to_review_final_eval.count()
    approved_final_eval_count = educators_approved_final_eval.count()

    return [final_eval_count, incomplete_final_eval_count, pending_final_eval_count, to_review_final_eval_count, approved_final_eval_count]


# Gather data for the evaluation step statistics and send to template    
class EvaluationStepCustomView(UnfoldModelAdminViewMixin, TemplateView):
    title = "Έλεγχος αξιολόγησης" 
    permission_required = ()
    template_name = "admin/consultant_checks.html"

    def get_context_data(self, **kwargs):
        user = self.request.user
        has_elevated_privileges = user.groups.filter(name='Επόπτες').exists() or user.is_superuser

        context = super(EvaluationStepCustomView, self).get_context_data(**kwargs)
        educators = Teacher.objects.filter(is_active=True, participates=True) if has_elevated_privileges else \
            Teacher.objects.filter(is_active=True, participates=True, consultant=user)

        total_educators = educators.count()
        educators_without_steps = educators.filter(participates=True, teacher_evaluation_steps=None).count()
        educators_missing_2nd_meeting = educators.filter(participates=True).exclude(
            teacher_evaluation_steps__es_type_id=2).count()
        educators_missing_3rd_meeting = educators.filter(participates=True).exclude(
            teacher_evaluation_steps__es_type_id=3).count()
        educators_missing_final_eval = educators.filter(participates=True).exclude(
            teacher_evaluation_steps__es_type_id=4).count()
        
        first_meeting_stats = compute_step_statistics(educators, 1)
        second_meeting_stats = compute_step_statistics(educators, 2)
        third_meeting_stats = compute_step_statistics(educators, 3)
        final_eval_stats = compute_final_evaluation_statistics(educators)

        tbl_data = {
                "headers": [
                    "#",
                    "Κατηγορία Ελέγχου",
                    "Πλήθος",
                    "Σε εκκρεμότητα",
                    "Ληξιπρόθεσμες",
                    "Ολοκληρωμένες"
                ],
                "rows": [
                    ["1", "Εκπαιδευτικοί για Αξιολόγηση", total_educators, "---", "---", "---"],
                    ["2", "Εκπαιδευτικοί χωρίς προγραμματισμένη Προαξιολογική",  educators_without_steps, educators_without_steps, "---", "---"],
                    ["3", "Εκπαιδευτικοί χωρίς προγραμματισμένη 1η διδασκαλία",  educators_missing_2nd_meeting, educators_missing_2nd_meeting, "---", "---"],
                    ["4", "Εκπαιδευτικοί χωρίς προγραμματισμένη 2η διδασκαλία",  educators_missing_3rd_meeting, educators_missing_3rd_meeting, "---", "---"],
                    ["5", "Εκπαιδευτικοί χωρίς Τελική Αξιολόγηση",  educators_missing_final_eval, educators_missing_final_eval, "---", "---"],
                    ["6", "Εκπαιδευτικοί με προγραμματισμένη Προαξιολογική", *first_meeting_stats],
                    ["7", "Εκπαιδευτικοί με προγραμματισμένη 1η διδασκαλία", *second_meeting_stats],
                    ["8", "Εκπαιδευτικοί με προγραμματισμένη 2η διδασκαλία", *third_meeting_stats]
                ]
            }
        
        tbl_data2 = {
            "headers": [
                "#",
                "Πλήθος",
                "Σε εκκρεμότητα",
                "Για αναθεώρηση",
                "Προς έλεγχο",
                "Ελέγχθηκαν"
            ],
            "rows": [
                [
                    "1",
                    *final_eval_stats
                ]
            ]
        }

        chart_stats = json.dumps(
            {
                "labels": ['Σύνολο', 'Με Προαξιολογ.', 'Με 1η Διδασκ.', 'Με 2η Διδασκ.', 'Με Τελ.Αξιολ.'],
                "datasets": [
                    {
                        "data": [total_educators, first_meeting_stats[0], second_meeting_stats[0], third_meeting_stats[0]], 
                        "borderWidth": 1
                    }
                ],
            }
        )
        context['chart_stats'] = chart_stats
        context['table_data'] = tbl_data
        context['table_data2'] = tbl_data2
                
        return context


# Function to serve files located at /documents
@login_required
def serve_document(request, document_name, folder = None, year = None):
    try:
        # Construct the document path (replace 'documents' with your actual folder name)
        if folder and year:
            document_path = os.path.join(settings.MEDIA_ROOT, 'documents', year, folder, document_name)
        else:
            document_path = os.path.join(settings.MEDIA_ROOT, 'documents', document_name)

        with open(document_path, 'rb') as document:
            content = document.read()

        # Set the appropriate content type based on the file extension
        content_type, _ = mimetypes.guess_type(document_name)
        return HttpResponse(content, content_type=content_type)

    except (FileNotFoundError, PermissionError) as e:
        return HttpResponseNotFound(f'Error serving document: {e}')


# Adds a metakinhsh for the selected evaluation step
@login_required
@csrf_protect
@require_POST
def add_metakinhsh(request):
    try:
        if not is_member(request.user, 'Σύμβουλοι'):
            return JsonResponse({
                'success': False,
                'message': 'Μόνο Σύμβουλοι μπορούν να προσθέσουν Μετακίνηση.'
            }, status=400)
        # Retrieve consultant (User). If it does not exist, get request user id
        consultant_id = request.POST.get('consultant') or request.user.id
        consultant = User.objects.get(id=consultant_id)

        # Retrieve teacher with full details
        teacher_id = request.POST.get('teacher')
        teacher = Teacher.objects.get(id=teacher_id)

        # Retrieve es_type with title
        es_type_id = request.POST.get('es_type')
        es_type = EvaluationStepType.objects.get(id=es_type_id)
        
        # Parse date
        es_date = request.POST.get('es_date')
        converted_date = datetime.strptime(es_date, '%d/%m/%Y').date()

        # Get existing EvaluationStep id
        step_id = EvaluationStep.objects.get(consultant=consultant_id, teacher=teacher_id, es_type=es_type_id, es_date=converted_date).pk
        
        # Construct aitiologia
        aitiologia = f"{es_type.title}, {teacher.last_name} {teacher.first_name}"

        # Check if a similar Metakinhsh already exists
        existing_metakinhsh = Metakinhsh.objects.filter(
            consultant=consultant,
            date_from=converted_date,
            date_to=converted_date,
            aitiologia=aitiologia
        ).exists()
        
        if existing_metakinhsh:
            return JsonResponse({
                'success': False,
                'message': 'Μια παρόμοια μετακίνηση υπάρχει ήδη.'
            }, status=400)

        # Create Metakinhsh object
        metakinhsh = Metakinhsh.objects.create(
            consultant=consultant,
            metak_from='Ηράκλειο',
            metak_to=teacher.school,
            date_from=converted_date,
            date_to=converted_date,
            aitiologia=aitiologia,
            km=0,
            is_evaluation=True
        )

        # update Evaluation Step with newly created Metakinhsh
        EvaluationStep.objects.filter(pk=step_id).update(linked_metakinhsh=metakinhsh)

        return JsonResponse({
            'success': True,
            'message': 'Επιτυχής προσθήκη μετακίνησης!',
            'id': metakinhsh.id
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Δε βρέθηκε ο σύμβουλος'
        }, status=400)
    
    except Teacher.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Δε βρέθηκε ο εκπ/κός'
        }, status=400)
    
    except EvaluationStepType.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Δε βρέθηκε το βήμα αξιολόγησης'
        }, status=400)
    
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    
    except Exception as e:
        print(e)
        return JsonResponse({
            'success': False,
            'message': 'Προέκυψε ένα σφάλμα. Βεβαιωθείτε ότι έχετε αποθηκεύσει το βήμα αξιολόγησης.'
        }, status=500)


# Input evaluation data from axiologisi.minedu.gov.gr (file teacher-evaluation-grades.csv)
@staff_member_required
def import_evaluation_data(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Παρακαλώ ανεβάστε ένα αρχείο CSV.')
            return redirect('admin:symvouloi_evaluationdata_changelist')

        try:
            csv_text = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(csv_text)
            
            created_count = 0
            updated_count = 0
            errors = []
            missing_afms = []
            row_nr = 1

            for row in reader:
                row_nr += 1
                has_evaluation_data = any([
                    row.get('ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ Α1/Α'),
                    row.get('ΠΕΔΙΟ Α1/Α'),
                    row.get('ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ Α1/Α'),
                    row.get('ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ Α2'),
                    row.get('ΠΕΔΙΟ Α2'),
                    row.get('ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ Α2'),
                    row.get('ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ Β'),
                    row.get('ΠΕΔΙΟ B'),
                    row.get('ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ B')
                ])

                if not has_evaluation_data:
                    print(f"Μη επαρκή δεδομένα στη γραμμή {row_nr}.")
                    continue

                try:
                    teacher = Teacher.objects.get(afm=row['ΑΦΜ'])

                    consultant_a1 = None
                    consultant_a2 = None
                    consultant_b = None

                    # Handle consultant A1
                    if row.get('ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ Α1/Α'):
                        consultant_afm = row['ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ Α1/Α'].split(':')[0]
                        try:
                            consultant_a1_obj = User.objects.get(username=consultant_afm)
                            consultant_a1 = f'{consultant_a1_obj.last_name} {consultant_a1_obj.first_name}'
                        except User.DoesNotExist:
                            consultant_a1 = consultant_afm

                    # Handle consultant A2
                    if row.get('ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ Α2'):
                        consultant_afm = row['ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ Α2'].split(':')[0]
                        try:
                            consultant_a2_obj = User.objects.get(username=consultant_afm)
                            consultant_a2 = f'{consultant_a2_obj.last_name} {consultant_a2_obj.first_name}'
                        except User.DoesNotExist:
                            consultant_a2 = consultant_afm

                    # Handle consultant B
                    if row.get('ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ B'):
                        consultant_afm = row['ΑΝΑΓΝΩΡΙΣΤΙΚΟ ΕΚΚΡΕΜΟΤΗΤΑΣ B'].split(':')[0]
                        try:
                            consultant_b_obj = User.objects.get(username=consultant_afm)
                            consultant_b = f'{consultant_b_obj.last_name} {consultant_b_obj.first_name}'
                        except User.DoesNotExist:
                            consultant_b = consultant_afm

                    # Parse dates
                    a1_date = None
                    a2_date = None
                    b_date = None

                    if row.get('ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ Α1/Α'):
                        naive_date = datetime.strptime(row['ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ Α1/Α'], '%d/%m/%Y %H:%M')
                        a1_date = timezone.make_aware(naive_date)

                    if row.get('ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ Α2'):
                        naive_date = datetime.strptime(row['ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ Α2'], '%d/%m/%Y %H:%M')
                        a2_date = timezone.make_aware(naive_date)

                    if row.get('ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ B'):
                        naive_date = datetime.strptime(row['ΗΜΕΡΟΜΗΝΙΑ ΑΞΙΟΛΟΓΗΣΗΣ B'], '%d/%m/%Y %H:%M')
                        b_date = timezone.make_aware(naive_date)

                    # Check if evaluation data already exists for this teacher
                    evaluation_data, created = EvaluationData.objects.update_or_create(
                        teacher=teacher,
                        defaults={
                            'consultant_a1': consultant_a1,
                            'a1_result': row.get('ΠΕΔΙΟ Α1/Α'),
                            'a1_evaluation_date': a1_date,
                            'consultant_a2': consultant_a2,
                            'a2_result': row.get('ΠΕΔΙΟ Α2'),
                            'a2_evaluation_date': a2_date,
                            'consultant_b': consultant_b,
                            'b_result': row.get('ΠΕΔΙΟ B'),
                            'b_evaluation_date': b_date,
                            'permanent': True if row.get('ΜΟΝΙΜΟΠΟΙΗΣΗ') == 'ΝΑΙ' else False
                        }
                    )

                    # update Teacher if permanent
                    if row.get('ΜΟΝΙΜΟΠΟΙΗΣΗ') == 'ΝΑΙ':
                        teacher.is_permanent = True
                        teacher.save()
                        print(f'Ο εκπ/κός με {teacher.afm} ορίστηκε ως μόνιμος.')

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Teacher.DoesNotExist:
                    missing_afms.append(row['ΑΦΜ'])
                except Exception as e:
                    errors.append(f"Σφάλμα για εκπαιδευτικό με ΑΦΜ {row['ΑΦΜ']}: {str(e)}")

            if created_count > 0 or updated_count > 0:
                messages.success(request, f'Επιτυχής εισαγωγή {created_count} και ενημέρωση {updated_count} αξιολογήσεων.')
            if errors:
                messages.warning(request, f'Προέκυψαν {len(errors)} σφάλματα κατά την εισαγωγή.')
                for error in errors:
                    messages.error(request, error)
            if missing_afms:
                afm_list = ", ".join(missing_afms)
                messages.error(request, f"Οι παρακάτω εκπ/κοί δε βρέθηκαν: {afm_list}")
            if created_count == 0 or updated_count == 0:
                messages.error(request, f'Δεν έγινε καμία εισαγωγή.')


        except Exception as e:
            messages.error(request, f'Σφάλμα κατά την επεξεργασία του αρχείου: {str(e)}')
            return redirect('admin:symvouloi_evaluationdata_changelist')

    return redirect('admin:symvouloi_evaluationdata_changelist')
