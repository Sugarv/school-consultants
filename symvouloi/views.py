import json
import os
import mimetypes
import requests
from datetime import datetime
from django.utils import timezone

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
from .models import TeacherAssignment, Teacher, EvaluationStep, EvaluationStepType

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


def dashboard_callback(request, context):
    ekp_cnt = Teacher.objects.all().count() if request.user.is_superuser else Teacher.objects.filter(consultant=request.user).count()
    step_cnt = EvaluationStep.objects.all().count() if request.user.is_superuser else EvaluationStep.objects.filter(consultant=request.user).count()
    is_elevated = request.user.groups.filter(name='Επόπτες').exists() or request.user.is_superuser

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
                consultant = User.objects.create_user(
                    username=consultant_afm,
                    password=f"{consultant_afm}-pass",
                    first_name=assignment.consultant_first_name,
                    last_name=assignment.consultant_last_name,
                    is_staff=True
                )
                added_consultants += 1
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
                            is_active=True,
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
    steps = EvaluationStep.objects.all() if request.user.is_superuser else EvaluationStep.objects.filter(consultant=request.user)

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
                    ["2", "Εκπαιδευτικοί χωρίς προγραμματισμένη 1η συνάντηση",  educators_without_steps, educators_without_steps, "---", "---"],
                    ["3", "Εκπαιδευτικοί χωρίς προγραμματισμένη 2η συνάντηση",  educators_missing_2nd_meeting, educators_missing_2nd_meeting, "---", "---"],
                    ["4", "Εκπαιδευτικοί χωρίς προγραμματισμένη 3η συνάντηση",  educators_missing_3rd_meeting, educators_missing_3rd_meeting, "---", "---"],
                    ["5", "Εκπαιδευτικοί χωρίς Τελική Αξιολόγηση",  educators_missing_final_eval, educators_missing_final_eval, "---", "---"],
                    ["6", "Εκπαιδευτικοί με προγραμματισμένη 1η συνάντηση", *first_meeting_stats],
                    ["7", "Εκπαιδευτικοί με προγραμματισμένη 2η συνάντηση", *second_meeting_stats],
                    ["8", "Εκπαιδευτικοί με προγραμματισμένη 3η συνάντηση", *third_meeting_stats]
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
                "labels": ['Σύνολο', 'Με 1η Συν.', 'Με 2η Συν.', 'Με 3η Συν.', 'Με Τελ.Αξιολ.'],
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