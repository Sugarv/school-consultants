from django.contrib import admin
from import_export.admin import ExportActionModelAdmin
from import_export import resources, fields
from django.contrib.auth.models import User
from import_export.widgets import ForeignKeyWidget
from unfold.admin import ModelAdmin, TabularInline
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from .views import MetakinhshCustomView, apofasi_metakinhshs_preview, katastash_plhrwmhs
from django.contrib import messages
from unfold.contrib.filters.admin import RelatedDropdownFilter
from unfold.contrib.import_export.forms import ExportForm
from app.filters import MyRangeDateFilter
from .models import Metakinhsh, Consultant, OfficeSchedule
from app.utils import is_member, is_member_of_many
from unfold.decorators import action
from django import forms
from django.utils.safestring import mark_safe


# Resource for import export plugin
class MetakinhshResource(resources.ModelResource):
    # used to declare foreign key @ field person
    consultant = fields.Field(
        column_name='consultant',
        attribute='consultant',
        widget=ForeignKeyWidget(User, field='id'))
    
    class Meta:
        model = Metakinhsh
        exclude = ('id',)
    
    # use dehydrate to display full name instead of person id
    def dehydrate_person(self, metakinhsh):
        full_name = getattr(metakinhsh.consultant, 'last_name') + ' ' + getattr(metakinhsh.consultant, 'first_name')
        return '%s' % full_name


class MetakinhshAdmin(ModelAdmin, ExportActionModelAdmin):
    resource_class = MetakinhshResource
    list_display_links = ('get_user','date_from','id','metak_to')
    list_filter_submit = True
    list_filter = [
        ("date_from", MyRangeDateFilter),
        # ("km", RangeNumericFilter),
        # ("person__last_name", DropdownFilter)
    ]
    search_fields = ['metak_to']
    list_per_page=25
    actions = ['apofasi_metakinhshs', 'apofasi_metakinhshs_oikon', 'katastash_plhrwmhs']
    ordering = ['-date_from']
    date_hierarchy = ('date_from')
    export_form_class = ExportForm

    class Media:
        js = ('js/script_metak.js',) 

    # construct get_user column to display full name
    def get_user(self, obj):
        return f'{obj.consultant.last_name} {obj.consultant.first_name}'
    get_user.short_description = 'Χρήστης'
    get_user.admin_order_field = 'consultant__last_name'

    def get_list_filter(self, request):
        if is_member(request.user,'Σύμβουλοι'):
            return (("date_from", MyRangeDateFilter),'pragmat', 'egkrish')
        return (
                ("date_from", MyRangeDateFilter),#("km", RangeNumericFilter),
                ('consultant', RelatedDropdownFilter), 'pragmat', 'egkrish', 'handler'
            )

    def get_list_display(self, request):
        if is_member(request.user,'Σύμβουλοι'):
            return ('id', 'metak_to', 'date_from', 'approved_display','complete_display','km','handler','is_evaluation')
        else:
            return ('id', 'get_user', 'metak_to', 'date_from', 'approved_display','complete_display','km','handler','is_evaluation')

    def get_readonly_fields(self, request, obj=None):
        is_supervisor = is_member_of_many(request.user, 'Επόπτες,Γραμματεία') or request.user.is_superuser
        is_consultant = is_member(request.user,'Σύμβουλοι')
        
        if obj and is_supervisor:
            return ('consultant','pragmat')
        elif is_consultant:
            # allow consultant to set pragmat only if egkrish is set
            if obj and obj.egkrish:
                return ('consultant', 'egkrish')
            else:
                return ('consultant', 'egkrish', 'pragmat')
        elif is_member(request.user,'Οικονομικό'):
            return ('consultant','egkrish','aitiologia')
        else:
            return super(MetakinhshAdmin, self).get_readonly_fields(request, obj=obj)
        
    # add url for custom view
    # see: https://unfoldadmin.com/docs/pages/
    def get_urls(self):
        return super().get_urls() + [
            path(
                "metakinhsh-calendar",
                MetakinhshCustomView.as_view(model_admin=self),
                name="metakinhsh_calendar"
            ),
            path('apofasi_metakinhshs/', apofasi_metakinhshs_preview, name='apofasi_metakinhshs_preview'),
            path('katastash_plhrwmhs/', katastash_plhrwmhs, name='katastash_plhrwmhs'),
        ]
    
    def get_queryset(self, request):
        # Get the default queryset
        qs = super().get_queryset(request)

        is_supervisor = is_member_of_many(request.user, 'Επόπτες,Οικονομικό,Γραμματεία') or request.user.is_superuser
        is_consultant = request.user.groups.filter(name='Σύμβουλοι').exists()
        
        # Check if the user is in the 'symvouloi' group
        if is_consultant:
            return qs.filter(consultant=request.user)
        
        # Check if the user is a superuser or in the 'directors' group
        elif is_supervisor:
            return qs

        # Return an empty queryset by default
        return qs.none()
    
    def get_fieldsets(self, request, obj=None):
        # If the user is in the 'symvouloi' group, make 'consultant' and 'es_type' fields read-only
        if is_member(request.user, 'Σύμβουλοι'):
            return [
                ( None, {
                    "fields" : [('metak_from', 'metak_to'),('date_from', 'date_to'), 'km', 'egkrish', 'pragmat','aitiologia','file']
                })
            ]
        elif is_member(request.user, 'Οικονομικό'):
            return [
                ( None, {
                    "fields" : [('metak_from', 'metak_to'),('date_from', 'date_to'), 'km', 'egkrish', 'pragmat','aitiologia', 
                                ('to_pay', 'amount1'), ('away', 'amount2'), 'is_evaluation'
                                # ('tickets', 'amount3'), ('stay', 'amount4'), 'special'
                                ]
                })
            ]
        return [
            ( None, {
                 "fields" : ['consultant', ('metak_from', 'metak_to'),('date_from', 'date_to'), 'km', 'egkrish', 'pragmat','aitiologia','is_evaluation']
            }) 
        ]
    
    
    def save_model(self, request, obj, form, change):
        """
        Set the `consultant` field to the logged-in user when saving a new EvaluationStep instance.
        """
        if not obj.pk:  # Only set consultant for new objects
            if request.user.groups.filter(name='Σύμβουλοι').exists():
                obj.consultant = request.user
        # Check if step for teacher already exists when a new object is saved
        if not change:
            if Metakinhsh.objects.filter(consultant=request.user, date_from=obj.date_from).exists():
                messages.error(request, "Σφάλμα: Έχει ήδη καταχωρηθεί η μετακίνηση γι' αυτήν την ημερομηνία.")
                return  # Abort saving

        super().save_model(request, obj, form, change)


    # Hide the action from unauthorized users
    def get_actions(self, request):
        actions = super().get_actions(request)

        # Remove the action if the user is not in the required group
        required_group_name = "Γραμματεία"  # Replace with your group's name
        if not (request.user.groups.filter(name=required_group_name).exists() or request.user.is_superuser):
            if 'apofasi_metakinhshs' in actions:
                del actions['apofasi_metakinhshs']

        # Remove the action if the user is not in the required group
        required_group_name = "Οικονομικό"  # Replace with your group's name
        if not (request.user.groups.filter(name=required_group_name).exists() or request.user.is_superuser):
            if 'apofasi_metakinhshs_oikon' in actions:
                del actions['apofasi_metakinhshs_oikon']

        return actions


    # Add action to issue Metakinhsh decision    
    @action(description="Απόφαση μετακίνησης")
    def apofasi_metakinhshs(self, request, queryset):
        """
        Custom action to redirect to a page for assigning selected users to a group.
        """
        # Get the selected user IDs
        metakinhsh_ids = queryset.values_list('id', flat=True)
        metakinhsh_ids_str = ",".join(map(str, metakinhsh_ids))  # Convert to a comma-separated string

        # Redirect to the group assignment page, passing selected user IDs as query parameters
        url = reverse('apofasi_metakinhshs') + f'?metakinhsh_ids={metakinhsh_ids_str}'
        return HttpResponseRedirect(url)
    
    @action(description="Έγκριση μετακίνησης εκτός έδρας")
    def apofasi_metakinhshs_oikon(self, request, queryset):
        """
        Custom action to redirect to a page for assigning selected users to a group.
        """
        # Get the selected user IDs
        metakinhsh_ids = queryset.values_list('id', flat=True)
        metakinhsh_ids_str = ",".join(map(str, metakinhsh_ids))  # Convert to a comma-separated string

        # Redirect to the group assignment page, passing selected user IDs as query parameters
        url = reverse('apofasi_metakinhshs') + f'?metakinhsh_ids={metakinhsh_ids_str}&oikon=1'
        return HttpResponseRedirect(url)
    
    @action(description="Κατάσταση πληρωμής")
    def katastash_plhrwmhs(self, request, queryset):
        """
        Custom action to redirect to a page for assigning selected users to a group.
        """
        # Get the selected user IDs
        metakinhsh_ids = queryset.values_list('id', flat=True)
        metakinhsh_ids_str = ",".join(map(str, metakinhsh_ids))  # Convert to a comma-separated string

        # Redirect to the group assignment page, passing selected user IDs as query parameters
        url = reverse('katastash_plhrwmhs') + f'?metakinhsh_ids={metakinhsh_ids_str}'
        return HttpResponseRedirect(url)
    

    # Fix: Display custom messages instead of True/False
    def complete_display(self, obj):
        return "Ναι" if obj.pragmat else "Όχι"

    def approved_display(self, obj):
        return "Ναι" if obj.egkrish else "Όχι"

    complete_display.short_description = "Ολοκληρώθηκε"
    approved_display.short_description = "Εγκρίθηκε"

admin.site.register(Metakinhsh, MetakinhshAdmin)


# Inline for User model
class ConsultantInline(TabularInline):
    model = Consultant
    extra = 0



class OfficeScheduleForm(forms.ModelForm):
    class Meta:
        model = OfficeSchedule
        fields = '__all__'
        widgets = {
            'days_in_office': forms.TextInput(attrs={'class': 'multidatepicker'}),
        }

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'https://code.jquery.com/ui/1.12.1/jquery-ui.min.js',
            'js/jquery-ui.multidatespicker.js',  # Ensure this path is correct
            'js/office_schedule.js',  # Custom JS to initialize the datepicker
        )
        css = {
            'all': ('https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css','css/jquery-ui.multidatespicker.css')
        }

class OfficeScheduleAdmin(ModelAdmin):
    form = OfficeScheduleForm
    list_display = ('consultant', 'month', 'days_total')

    def days_total(self, obj):
        return (len(obj.days_in_office))


    def has_add_permission(self, request):
        return request.user.groups.filter(name='Σύμβουλοι').exists() or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name='Σύμβουλοι').exists() or request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to determine and set the Greek month name
        based on the `days_in_office` JSON data.
        """
        import calendar
        from django.utils.translation import gettext as _

        if obj.days_in_office:
            # Assume days_in_office contains dates in the format: ['YYYY-MM-DD', ...]
            first_date = obj.days_in_office[0]  # Take the first date
            month_number = int(first_date.split("-")[1])  # Extract the month number

            # Map to Greek month name
            greek_months = [
                _("Ιανουάριος"), _("Φεβρουάριος"), _("Μάρτιος"),
                _("Απρίλιος"), _("Μάιος"), _("Ιούνιος"),
                _("Ιούλιος"), _("Αύγουστος"), _("Σεπτέμβριος"),
                _("Οκτώβριος"), _("Νοέμβριος"), _("Δεκέμβριος")
            ]
            obj.month = greek_months[month_number - 1]

        # Save the object
        super().save_model(request, obj, form, change)

admin.site.register(OfficeSchedule, OfficeScheduleAdmin)