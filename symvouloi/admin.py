from django.contrib import admin
from .models import (
    Teacher,
    EvaluationStepType,
    EvaluationStep,
    TeacherAssignment,
    EvaluationData,
)
from django.contrib.auth.models import User, Group
from django.contrib.auth import views as auth_views
from django.contrib.admin.models import LogEntry
from unfold.admin import ModelAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from import_export.admin import ImportExportModelAdmin, ExportActionModelAdmin
from unfold.admin import StackedInline
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.contrib import messages
from unfold.decorators import action, display
from .views import assign_users_to_group, EvaluationStepCustomView, import_evaluation_data
from unfold.contrib.filters.admin import (RelatedDropdownFilter)
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from django.utils.html import format_html
from app.filters import MyRangeDateFilter
from app.utils import is_member, is_member_of_many
from django.contrib.auth.hashers import make_password
from metakinhseis.admin import ConsultantInline
from django.utils import timezone


# Inline for Evaluation Steps in TeacherAdmin
class EvaluationStepInline(StackedInline):
    model = EvaluationStep
    tab = True
    extra = 0
    show_change_link = True
    fields = ['es_type', 'es_date', 'category']

    def get_queryset(self, request):
        # Get the default queryset
        qs = super().get_queryset(request)
        
        # Check if the user is in the 'symvouloi' group
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return qs.filter(teacher__consultant=request.user)
        
        # Check if the user is a superuser or in the 'directors' group
        elif request.user.is_superuser or request.user.groups.filter(name='Επόπτες').exists():
            return qs

        # Return an empty queryset by default
        return qs.none()


# Inline for Evaluation Data (History) in TeacherAdmin
class EvaluationDataInline(StackedInline):
    model = EvaluationData
    tab = True
    extra = 0
    fieldsets = [
        ( None, {
            "fields" : [('consultant_a1', 'a1_result','a1_evaluation_date'), 
                        ('consultant_a2', 'a2_result','a2_evaluation_date'),
                        ('consultant_b', 'b_result','b_evaluation_date'),
                        'permanent'
                        ]
        })
    ]
    can_delete = False

    def get_queryset(self, request):
        # Get the default queryset
        qs = super().get_queryset(request)
        
        # Get the parent id
        parent_object_id = request.resolver_match.kwargs.get('object_id')
        
        return qs.filter(teacher__pk=parent_object_id)
        
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]
    
    def has_add_permission(self, request, obj=None):
        return False  # Disable "Add" button
    def has_delete_permission(self, request, obj=None):
        return False  # Disable "Delete" 


###########################
######### Teacher #########
###########################
@admin.register(Teacher)
class TeacherAdmin(ModelAdmin, ImportExportModelAdmin):
    ordering = ('id',)
    search_fields = ('afm', 'last_name', 'first_name')
    list_filter_submit = True
    list_display_links = ('afm', 'last_name')
    inlines = [EvaluationStepInline, EvaluationDataInline]
    export_form_class = ExportForm
    import_form_class = ImportForm
    actions = ['update_teachers']
    list_per_page = 50

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "consultant":
            kwargs["queryset"] = User.objects.order_by('last_name', 'first_name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        # Get the default queryset
        qs = super().get_queryset(request)
        
        # Check if the user is in the 'symvouloi' group
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return qs.filter(consultant__username=request.user.username)
        
        # Check if the user is a superuser or in the 'directors' group
        elif request.user.is_superuser or request.user.groups.filter(name='Επόπτες').exists():
            return qs

        # Return an empty queryset by default
        return qs.none()
    
    def get_list_filter(self, request):
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return ('participates', 'is_permanent', 'specialty')
        return [('consultant',RelatedDropdownFilter), 'participates', 'is_permanent', 'specialty' ]
    
    def get_list_display(self, request):
        # If user is in 'symvouloi' group, show specific fields
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return ('afm', 'last_name', 'first_name', 'specialty', 'participates_display', 'is_active_display', 'is_permanent_display')
        # For other users, show all fields including 'consultant'
        return ('afm', 'last_name', 'first_name', 'consultant_last_name', 'specialty', 'participates_display', 'is_active_display', 'is_permanent_display')
    
    # Display custom messages instead of True/False
    @display(label={ 'OXI': "danger", 'NAI': "success" },)
    def participates_display(self, obj):
        return "NAI" if obj.participates else "OXI"
    
    @display(label={ 'OXI': "danger", 'NAI': "success" },)
    def is_active_display(self, obj):
        return "NAI" if obj.is_active else "OXI"
    
    @display(label={ 'OXI': "danger", 'NAI': "success" },)
    def is_permanent_display(self, obj):
        return "NAI" if obj.is_permanent else "OXI"

    participates_display.short_description = "Συμμετέχει"
    is_active_display.short_description = "Ενεργός"
    is_permanent_display.short_description = "Μονιμοποίηση"

    # Correctly display consultant last name
    def consultant_last_name(self, obj):
        """
        Custom display method for consultant's last name.
        """
        return obj.consultant.last_name if obj.consultant else "—"  # Return a dash if no consultant is assigned

    consultant_last_name.short_description = "Επώνυμο Συμβούλου"
    
    def save_formset(self, request, form, formset, change):
        """
        Override save_formset to automatically set `consultant` and `teacher` fields
        when saving EvaluationStep inline instances.
        """
        instances = formset.save(commit=False)  # Prevent immediate save
        for instance in instances:
            if isinstance(instance, EvaluationStep):  # Check if the instance is of the right type
                instance.consultant = request.user  # Set the consultant to the logged-in user
                instance.teacher = form.instance  # Set the teacher to the parent Teacher instance
                instance.save()  # Save the instance
        formset.save_m2m()  # Save any many-to-many relationships

    def get_fieldsets(self, request, obj=None):
        # If the user is in the 'symvouloi' group, make 'consultant' and 'es_type' fields read-only
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return [
                ( None, {
                    "fields" : ['afm',('last_name', 'first_name'), ('father_name', 'specialty'), 'school', ('fek', 'appointment_date'), ('mobile', 'mail'),
                                ('participates', 'is_active', 'is_permanent'), 'comments']
                })
            ]
        return [
            ( None, {
                "fields": ['consultant','afm',('last_name', 'first_name'), ('father_name', 'specialty'), 'school', ('fek', 'appointment_date'), 
                           ('mobile', 'mail'), ('participates', 'is_active', 'is_permanent'), 'comments']
            }) 
        ]
    
    def get_readonly_fields(self, request, obj = ...):
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return ('afm','last_name', 'first_name', 'father_name', 'specialty', 'school', 'fek', 'appointment_date', 'mobile', 'mail', 'is_permanent')
        return ()
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        # Remove the action if the user is not in the required group
        if not (request.user.is_superuser):
            del actions ['update_teachers']
        return actions
    
    def update_teachers(self, request, queryset):
        """
        Custom action to call the `update_teachers` view.
        This action works without requiring selected objects.
        """
        try:
            # Directly call the view that processes the update (you can also import the view)
            from .views import update_teachers  # Adjust this import as needed
            # Call the view function directly (simulate a request)
            response = update_teachers(request)  # Pass request to view

            # Get the message from the response (if returned as part of the JsonResponse or response content)
            if hasattr(response, 'content'):
                message = response.content.decode('utf-8')  # Assuming the message is returned in response
                self.message_user(request, message, level=messages.SUCCESS)
            else:
                self.message_user(request, "Επιτυχής ενημέρωση εκπ/κών!", level=messages.SUCCESS)

        except Exception as e:
            self.message_user(request, f"Απέτυχε ο συγχρονισμός: {str(e)}", level=messages.ERROR)

    update_teachers.short_description = "Ενημέρωση εκπαιδευτικών (γενική ενέργεια)"
    update_teachers.acts_on_all = True


###################################
######### Evaluation Step #########
###################################
@admin.register(EvaluationStepType)
class EvaluationStepTypeAdmin(ModelAdmin):
    list_display = ('id', 'title')
    list_display_links = ('id', 'title')
    ordering = ('id',)

@admin.register(EvaluationStep)
class EvaluationStepAdmin(ModelAdmin, ExportActionModelAdmin):
    ordering = ('consultant__last_name', 'teacher', 'es_type')
    list_display_links = ('consfname', 'teacher', 'es_type')
    search_fields = (
        'consultant__afm', 'consultant__last_name', 'consultant__first_name',
        'teacher__afm', 'teacher__last_name', 'teacher__first_name')
    
    date_hierarchy = ('es_date')
    list_filter_submit = True
    list_filter = [
        ("es_date", MyRangeDateFilter),
    ]
    change_form_after_template = "admin/metakinhsh_change_form_after.html"
    export_form_class = ExportForm
    actions = ['mass_confirmation']
    list_per_page = 30

    def get_queryset(self, request):
        # Get the default queryset
        qs = super().get_queryset(request)
        
        # Check if the user is in the 'symvouloi' group
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return qs.filter(consultant__username=request.user.username)
        
        # Check if the user is a superuser or in the 'directors' group
        elif request.user.is_superuser or request.user.groups.filter(name='Επόπτες').exists():
            return qs

        # Return an empty queryset by default
        return qs.none()
    
    def get_fields(self, request, obj=None):
        fields = []
        # If the user is in the 'symvouloi' group
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            fields += ['consfname', 'teacher', 'es_type', 'es_date', 'complete', 'category', 'comments', 'linked_metakinhsh']
        else:
            fields += ['consultant','teacher', 'es_type', 'es_date', 'complete', 'category', 'comments', 'linked_metakinhsh']
        # if final step, add document & approved
        if obj and obj.es_type.pk == 4:
            fields += ['approved', 'evaluation_document']
        return fields
        
    def get_list_filter(self, request):
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return (('es_date', MyRangeDateFilter), 'es_type','complete','approved')
        return (('es_date', MyRangeDateFilter), 'es_type', ('teacher', RelatedDropdownFilter),('consultant', RelatedDropdownFilter), 'complete', 'approved')
    
    def get_list_display(self, request):
        # If user is in 'symvouloi' group, show specific fields
        if request.user.groups.filter(name='Σύμβουλοι').exists():
            return ('teacher', 'es_type', 'es_date', 'complete_display')
        # For other users, show all fields including 'consultant'
        return ('consfname', 'teacher', 'es_type', 'es_date', 'complete_display')
    
    # choose only from teachers with the current user as consultant
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher" and request.user.groups.filter(name='Σύμβουλοι').exists():
            # Filter teachers to only show those associated with the current user as a consultant
            kwargs["queryset"] = Teacher.objects.filter(consultant=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_readonly_fields(self, request, obj=None):
        readonly = ['consfname', 'file_link', 'linked_metakinhsh']
        if is_member(request.user, 'Σύμβουλοι'):
            readonly += ['comments_from_director', 'approved']
        return readonly
    
    def consfname(self, instance):
        return f"{instance.consultant.last_name} {instance.consultant.first_name}"
    
    consfname.short_description = 'Σύμβουλος'
    consfname.admin_order_field = 'consultant__last_name'
    
    def save_model(self, request, obj, form, change):
        """
        Set the `consultant` field to the logged-in user when saving a new EvaluationStep instance.
        """
        # Check if ts completed and appointment date is after today
        if obj.complete and obj.es_date >= timezone.now().date():
            messages.error(request, "Σφάλμα: Δεν μπορείτε να ορίσετε ως ολοκληρωμένο βήμα του οποίου η ημ/νία είναι μεταγενέστερη!")
            return

        if not obj.pk:  # Only set consultant for new objects
            if request.user.groups.filter(name='Σύμβουλοι').exists():
                obj.consultant = request.user
        # Check if step for teacher already exists when a new object is saved
        if not change:
            if EvaluationStep.objects.filter(teacher=obj.teacher, es_type=obj.es_type).exists():
                messages.error(request, "Σφάλμα: Υπάρχει ήδη αυτό το βήμα αξιολόγησης για αυτόν/-ην τον/-ην εκπ/κό.")
                return  # Abort saving

        super().save_model(request, obj, form, change)

    # add url for custom view
    # see: https://unfoldadmin.com/docs/pages/
    def get_urls(self):
        return super().get_urls() + [
            path(
                "evaluation-check",
                EvaluationStepCustomView.as_view(model_admin=self),
                name="evaluation_check"
            ),
        ]
    
    # Fix: Display custom messages instead of True/False
    @display(label={ 'OXI': "danger", 'NAI': "success" },)
    def complete_display(self, obj):
        return "NAI" if obj.complete else "OXI"

    @display(label={ 'OXI': "danger", 'NAI': "success" },)
    def approved_display(self, obj):
        return "NAI" if obj.approved else "OXI"

    complete_display.short_description = "Ολοκληρώθηκε"
    approved_display.short_description = "Εγκρίθηκε"

    @action(description="Μαζική έγκριση")
    def mass_confirmation(self, request, queryset):
        # Custom action to massively confirm evaluation steps
        try:
            queryset.update(approved=True)
            messages.success(request, 'Επιτυχής έγκριση βημάτων αξιολόγησης!')
        except:
            messages.error(request, 'Αποτυχία έγκρισης βημάτων αξιολόγησης')

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Remove the action if the user is not in the required group
        if not (is_member(request.user, 'Επόπτες') or request.user.is_superuser):
            del actions ['mass_confirmation']

        return actions


#####################################
######### TeacherAssignment #########
#####################################
@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ('teacher_afm', 'teacher_last_name', 'consultant_afm', 'consultant_last_name', 'loaded')
    actions = ['sync_teachers_and_consultants']
    list_filter = ['loaded']

    def sync_teachers_and_consultants(self, request, queryset):
        """
        Custom action to call the `update_teacher_and_consultant` view.
        This action works without requiring selected objects.
        """
        try:
            # Directly call the view that processes the update (you can also import the view)
            from .views import update_teacher_and_consultant  # Adjust this import as needed
            # Call the view function directly (simulate a request)
            response = update_teacher_and_consultant(request)  # Pass request to view

            # Get the message from the response (if returned as part of the JsonResponse or response content)
            if hasattr(response, 'content'):
                message = response.content.decode('utf-8')  # Assuming the message is returned in response
                self.message_user(request, message, level=messages.SUCCESS)
            else:
                self.message_user(request, "Επιτυχής συγχρονισμός εκπ/κών - συμβούλων εκπ/σης!", level=messages.SUCCESS)

        except Exception as e:
            self.message_user(request, f"Απέτυχε ο συγχρονισμός: {str(e)}", level=messages.ERROR)
    
    

    sync_teachers_and_consultants.short_description = "Συγχρονισμός Εκπαιδευτικών και Συμβούλων (γενική ενέργεια)"
    sync_teachers_and_consultants.acts_on_all = True


class NewUserAdmin(ModelAdmin):
    list_display = ('username', 'last_name', 'first_name', 'auth_groups', 'show_impersonate_link')
    actions = ['assign_to_group']
    search_fields = ('last_name',)
    fieldsets = [
        ( None, {
            "fields" : ['username', 'password', ('last_name', 'first_name'), 'email', ('is_staff','is_active'), 'is_superuser', 'groups']
        })
    ]

    # Show consultant inline only for supervisor & consultants
    def get_inlines(self, request, obj=None):
        return [ConsultantInline] if obj and (is_member_of_many(request.user, 'Σύμβουλοι,Επόπτες') or request.user.is_superuser) else []

    def auth_groups(self, obj):
        # Fetch all groups for the user and join their names as a string
        return ", ".join([group.name for group in obj.groups.all()])
    
    @action(description="Ανάθεση χρηστών σε ομάδα")
    def assign_to_group(self, request, queryset):
        """
        Custom action to redirect to a page for assigning selected users to a group.
        """
        # Get the selected user IDs
        user_ids = queryset.values_list('id', flat=True)
        user_ids_str = ",".join(map(str, user_ids))  # Convert to a comma-separated string

        # Redirect to the group assignment page, passing selected user IDs as query parameters
        url = reverse('admin:assign_users_to_group') + f'?user_ids={user_ids_str}'
        return HttpResponseRedirect(url)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('assign_users_to_group/', assign_users_to_group, name='assign_users_to_group'),
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        """
        Override save_model to encode the password if it's being set or updated.
        """
        if 'password' in form.changed_data:
            obj.password = make_password(obj.password)  # Ensure the password is hashed
        super().save_model(request, obj, form, change)
    
    def __str__(self):
        return f'{self.last_name} {self.first_name}'
    
    def show_impersonate_link(self, obj):
        url = reverse('impersonate-start', args=[obj.pk])
        return format_html('<a href="{}">Ενεργοποίηση</a>', url)
    show_impersonate_link.short_description = 'Μίμηση χρήστη'
    
    auth_groups.short_description = "Ομάδες"

# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, NewUserAdmin)

class NewGroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

admin.site.unregister(Group)
admin.site.register(Group, NewGroupAdmin)

# Add LogEntry to admin to monitor history log
class LogEntryAdmin(admin.ModelAdmin):
    """Log Entry admin interface."""
    date_hierarchy = "action_time"
    fields = (
        "action_time",
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )
    list_display = (
        "action_time",
        "user",
        "action_message",
        "content_type",
        "object_link",
    )
    list_filter = (
        "action_flag",
        ("content_type", admin.RelatedOnlyFieldListFilter),
        ("user", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "object_repr",
        "change_message",
    )
    def object_link(self, obj):
        """Returns the admin link to the log entry object if it exists."""
        admin_url = None if obj.is_deletion() else obj.get_admin_url()
        if admin_url:
            return format_html('<a href="{}">{}</a>', admin_url, obj.object_repr)
        else:
            return obj.object_repr
    object_link.short_description = "object"
    def action_message(self, obj):
        """
        Returns the action message.
        Note: this handles deletions which don't return a change message.
        """
        change_message = obj.get_change_message()
        # If there is no change message then use the action flag label
        if not change_message:
            change_message = f"{obj.get_action_flag_display()}."
        return change_message
    action_message.short_description = "action"
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("content_type")
    def has_add_permission(self, request):
        """Log entries cannot be added manually."""
        return False
    def has_change_permission(self, request, obj=None):
        """Log entries cannot be changed."""
        return False
    def has_delete_permission(self, request, obj=None):
        """Log entries can only be deleted when the setting is enabled."""
        return False #DJANGO_ADMIN_LOGS_DELETABLE and super().has_delete_permission(
            #request, obj
        #)
    # Prevent changes to log entries creating their own log entries!
    def log_addition(self, request, obj, message):
        pass
    def log_change(self, request, obj, message):
        pass
    def log_deletion(self, request, obj, object_repr):
        pass
    # TODO: decode unicode messages in logentry
    # # decoded_string = json.loads(unicode_string.encode('utf-8').decode('unicode_escape'))
# Register the LogEntry admin if enabled
admin.site.register(LogEntry, LogEntryAdmin)


@admin.register(EvaluationData)
class EvaluationDataAdmin(ModelAdmin):
    list_display = ('teacher', 'consultant_a1', 'a1_evaluation_date', 'consultant_a2', 'a2_evaluation_date', 'consultant_b', 'b_evaluation_date', 'permanent')
    list_filter = ('permanent', ('teacher', RelatedDropdownFilter))
    search_fields = ('teacher__afm', 'teacher__last_name', 'teacher__first_name')
    readonly_fields = ('teacher', 'consultant_a1', 'a1_result', 'a1_evaluation_date', 
                      'consultant_a2', 'a2_result', 'a2_evaluation_date',
                      'consultant_b', 'b_result', 'b_evaluation_date', 'permanent')
    fieldsets = [
        ( None, {
            "fields" : [('consultant_a1', 'a1_result','a1_evaluation_date'), 
                        ('consultant_a2', 'a2_result','a2_evaluation_date'),
                        ('consultant_b', 'b_result','b_evaluation_date'),
                        'permanent'
                        ]
        })
    ]
    date_hierarchy = ('a1_evaluation_date')
    list_filter_submit = True
    list_after_template = "admin/evaluationdata_change_form_after.html"
    list_per_page = 30
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', import_evaluation_data, name='import_evaluation_data'),
        ]
        return custom_urls + urls
    
    def has_add_permission(self, request):
        return False  # Disable manual creation - data should only be imported
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete records
    
    def has_change_permission(self, request, obj=None):
        return False  # Data should be read-only once imported
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context=extra_context)


class UnfoldPasswordResetView(auth_views.PasswordResetView):
    template_name = 'admin/password_reset_form.html'

class UnfoldPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'admin/password_reset_done.html'

class UnfoldPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'admin/password_reset_confirm.html'

class UnfoldPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'admin/password_reset_complete.html'
