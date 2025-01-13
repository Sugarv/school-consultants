from django import forms

# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Layout, Submit, Fieldset
# from crispy_forms.bootstrap import TabHolder, Tab, Div, Field
from datetime import date, timedelta

from .models import Metakinhsh


class MetakinhshForm(forms.ModelForm):
    class Meta:
        model = Metakinhsh
        fields = '__all__'
        exclude = ['person','handler']
    
    # if egkrish is set, disallow update
    # allow only when user sets pragmat
    def clean(self):
        cleaned_data = super().clean()
        egkrish = cleaned_data.get('egkrish')
        date_from = cleaned_data.get('date_from')
        instance = getattr(self, 'instance', None)

        if not instance.pk and date_from and date_from < date.today():
            raise forms.ValidationError("Σφάλμα: Παρακαλώ επιλέξτε μια μελλοντική ημερομηνία.")

        if egkrish and instance and not 'pragmat' in self.changed_data:
            raise forms.ValidationError("Σφάλμα: Δεν μπορούν να γίνουν αλλαγές αφού εγκριθεί η μετακίνηση. Παρακαλώ επικοινωνήστε με τη διαχείριση...")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')
        future_date = date.today() + timedelta(days=7)  # Replace X with the desired number of days

        self.fields['egkrish'].disabled = True

        # Disable pragmat if the instance is new or if egkrish is not set
        if not self.instance.pk or not self.instance.egkrish:
            self.fields['pragmat'].disabled = True

        # if edit, allow all dates
        if instance:
            self.fields['date_from'].widget = forms.widgets.DateInput(
                attrs={
                    'type': 'date', 
                    'placeholder': 'yyyy-mm-dd (DOB)',
                    'class': 'form-control',
                    },
                format="%Y-%m-%d"
            )
            self.fields['date_to'].widget = forms.widgets.DateInput(
                attrs={
                    'type': 'date', 
                    'placeholder': 'yyyy-mm-dd (DOB)',
                    'class': 'form-control',
                    },
                format="%Y-%m-%d"
            )
        # else allow only future dates +7 days from today
        else:
            self.fields['date_from'].widget = forms.widgets.DateInput(
                attrs={
                    'type': 'date', 
                    'placeholder': 'yyyy-mm-dd (DOB)',
                    'class': 'form-control',
                    'min': future_date.strftime("%Y-%m-%d"),  # Set the minimum selectable date as the future date
                    },
                format="%Y-%m-%d"
            )
            self.fields['date_to'].widget = forms.widgets.DateInput(
                attrs={
                    'type': 'date', 
                    'placeholder': 'yyyy-mm-dd (DOB)',
                    'class': 'form-control',
                    'min': future_date.strftime("%Y-%m-%d"),  # Set the minimum selectable date as the future date
                    },
                format="%Y-%m-%d"
            )
        # self.helper = FormHelper()
        # self.helper.form_class = 'form-horizontal'
        # self.helper.label_class = 'col-lg-4'
        # self.helper.field_class = 'col-lg-8'
        # self.helper.form_method = 'post'
        # self.helper.add_input(Submit('submit', 'Αποθήκευση'))