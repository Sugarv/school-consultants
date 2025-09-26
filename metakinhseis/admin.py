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
from app.utils import is_member, is_member_of_many, get_school_year, get_current_school_year
from unfold.decorators import action, display
from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.conf import settings
import json


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
        'school_year',
    ]
    search_fields = ['metak_to','consultant__last_name']
    list_per_page=25
    actions = ['apofasi_metakinhshs', 'apofasi_metakinhshs_oikon', 'katastash_plhrwmhs', 'mass_confirmation']
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
            return (("date_from", MyRangeDateFilter),'pragmat', 'egkrish', 'school_year')
        return (
                ("date_from", MyRangeDateFilter),#("km", RangeNumericFilter),
                ('consultant', RelatedDropdownFilter), 'pragmat', 'egkrish', 'handler', 'school_year'
            )

    def get_list_display(self, request):
        if is_member(request.user,'Σύμβουλοι'):
            return ('id', 'metak_to', 'date_from', 'approved_display','complete_display','km','handler','is_evaluation', 'school_year')
        else:
            return ('id', 'get_user', 'metak_to', 'date_from', 'approved_display','complete_display','km','handler','is_evaluation', 'school_year')

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
        qs = super().get_queryset(request)

        is_supervisor = (
            is_member_of_many(request.user, 'Επόπτες,Οικονομικό,Γραμματεία')
            or request.user.is_superuser
        )
        is_consultant = request.user.groups.filter(name='Σύμβουλοι').exists()
        
        if is_consultant:
            return qs.filter(consultant=request.user)
        elif is_supervisor:
            return qs
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
        # Set the school_year
        if obj and obj.date_from:
            obj.school_year = get_school_year(obj.date_from)
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
        if not (is_member(request.user, "Γραμματεία") or request.user.is_superuser):
            del actions['apofasi_metakinhshs']

        # Remove the action if the user is not in the required group
        if not (is_member(request.user, "Οικονομικό") or request.user.is_superuser):
            del actions['apofasi_metakinhshs_oikon']
            del actions['katastash_plhrwmhs']

        # Hide mass_confirmation from FinDep, Consultants, Secretariat
        if is_member_of_many(request.user, 'Οικονομικό,Σύμβουλοι,Γραμματεία'):
            del actions['mass_confirmation']        

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
    
    @action(description="Μαζική έγκριση")
    def mass_confirmation(self, request, queryset):
        # Custom action to massively confirm transfers
        try:
            queryset.update(egkrish=True)
            messages.success(request, 'Επιτυχής έγκριση μετακινήσεων!')
        except:
            messages.error(request, 'Αποτυχία έγκρισης μετακινήσεων')
    

    # Fix: Display custom messages instead of True/False
    @display(label={ 'OXI': "danger", 'NAI': "success" },)
    def complete_display(self, obj):
        return "NAI" if obj.pragmat else "OXI"

    @display(label={ 'OXI': "danger", 'NAI': "success" },)
    def approved_display(self, instance: Metakinhsh):
        return "NAI" if instance.egkrish else "OXI"

    complete_display.short_description = "Ολοκληρώθηκε"
    approved_display.short_description = "Εγκρίθηκε"

    def changelist_view(self, request, extra_context=None):
        # If a year is selected, filter the queryset by that year
        if request.GET.get('school_year__exact') and request.GET.get('school_year'):
            q = request.GET.copy()
            q['school_year__exact'] = request.GET.get('school_year')
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
            current_school_year = request.GET.get('school_year')
            
        # If nothing is selected, get the current school year queryset
        if not request.GET.get('school_year__exact') and not request.GET.get('q') and not request.GET.get('school_year'):
            current_school_year = get_current_school_year()
            q = request.GET.copy()
            q['school_year__exact'] = current_school_year
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Metakinhsh, MetakinhshAdmin)


# Inline for User model
class ConsultantInline(TabularInline):
    model = Consultant
    extra = 0



class OfficeScheduleForm(forms.ModelForm):
    class Meta:
        model = OfficeSchedule
        fields = '__all__'
        exclude = ['month']
        widgets = {
            'days_in_office': forms.TextInput(attrs={'class': 'multidatepicker'}),
        }
    
    def clean_days_in_office(self):
        data = self.cleaned_data['days_in_office']
        try:
            # Ensure the data is valid JSON
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, list):
                raise ValidationError("Days in office must be a list of dates.")

            # Trim each element in the list
            data = [date.strip() for date in data]

            return data
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON data.")
        

class OfficeScheduleAdmin(ModelAdmin):
    form = OfficeScheduleForm
    change_form_template = 'admin/office_schedule_change_form.html'  # Use the custom template
    list_display = ('consultant', 'month', 'days_total')
    list_display_links = ('consultant','month')
    search_fields = ['consultant', 'month']
    list_filter_submit = True
    ordering = ['-month']

    def has_module_permission(self, request):
        if not settings.SHOW_OFFICE_DAYS:
            return False
        return super().has_module_permission(request)

    def days_total(self, obj):
        return (len(obj.days_in_office))
    days_total.short_description = 'Σύνολο ημερών'

    def has_add_permission(self, request):
        return request.user.groups.filter(name='Σύμβουλοι').exists() or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name='Σύμβουλοι').exists() or request.user.is_superuser
    
    def get_list_filter(self, request):
        if is_member(request.user,'Σύμβουλοι'):
            return ("month",)
        return (
                ("month", ('consultant', RelatedDropdownFilter) )
        )
    
    def get_list_display(self, request):
        if is_member(request.user,'Σύμβουλοι'):
            return ('month', 'days_total')
        else:
            return ('consultant', 'month', 'days_total')
        
    def get_fieldsets(self, request, obj=None):
        # If the user is in the 'symvouloi' group, make 'consultant' and 'es_type' fields read-only
        if is_member(request.user, 'Σύμβουλοι'):
            return [
                ( None, {
                    "fields" : [('days_in_office',) ]
                })
            ]
        return [
            ( None, {
                 "fields" : ['consultant', 'days_in_office']
            }) 
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
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to determine and set the Greek month name
        based on the `days_in_office` JSON data. Ensures all dates are
        from the same month before saving.
        """
        if not obj.pk:  # Only set consultant for new objects
            if request.user.groups.filter(name='Σύμβουλοι').exists():
                obj.consultant = request.user
        if obj.days_in_office:
            try:
                # Extract unique (month, year) tuples from selected dates
                month_years = {(int(date.split("-")[1]), int(date.split("-")[0])) for date in obj.days_in_office}

                # If more than one unique (month, year) combination exists, show error
                if len(month_years) > 1:
                    messages.error(request, "Σφάλμα: Οι επιλεγμένες ημέρες δεν ανήκουν στον ίδιο μήνα!")
                    return

                # Extract the single (month, year) pair
                month_number, year = month_years.pop()

                # Map to Greek month name
                greek_months = [
                    "Ιανουάριος", "Φεβρουάριος", "Μάρτιος",
                    "Απρίλιος", "Μάιος", "Ιούνιος",
                    "Ιούλιος", "Αύγουστος", "Σεπτέμβριος",
                    "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"
                ]

                # Store in `month` field with both month name and year
                obj.month = f"{greek_months[month_number - 1]} {year}"

            except Exception as e:
                messages.error(request, "Σφάλμα κατά την επεξεργασία των ημερομηνιών!")
                return
        
        # Check for duplicate records (same consultant & month)
        if not obj.pk and OfficeSchedule.objects.filter(consultant=obj.consultant, month=obj.month).exclude(pk=obj.pk).exists():
            messages.error(request, "Σφάλμα: Υπάρχει ήδη ένα μηνιαίο πρόγραμμα γι' αυτόν τον σύμβουλο & μήνα!")
            return

        # Save the object
        super().save_model(request, obj, form, change)

admin.site.register(OfficeSchedule, OfficeScheduleAdmin)
