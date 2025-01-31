from django.db import models
from django.contrib.auth.models import User
# from users.models import CustomUser
from slugify import slugify
from solo.models import SingletonModel
import os


# Create your models here.
class Teacher(models.Model):
    evaluation_year = models.CharField(null=False, blank=False, max_length=10,verbose_name='Σχ. Έτος Αξιολόγησης')
    consultant = models.ForeignKey(User, null=False, on_delete=models.CASCADE,verbose_name='Σύμβουλος Εκπαίδευσης',related_name='evaluates_teachers')
    afm = models.CharField(null=False, blank=False, max_length=9, verbose_name='ΑΦΜ')
    last_name = models.CharField(null=False, blank=False, max_length=50, verbose_name='Επώνυμο')
    first_name = models.CharField(null=False, blank=False, max_length=50, verbose_name='Όνομα')
    father_name = models.CharField(null=True, blank=True, max_length=50, verbose_name='Πατρώνυμο')
    specialty = models.CharField(null=True, blank=True, max_length=10, verbose_name='Ειδικότητα')
    school = models.CharField(null=True, blank=True, max_length=100, verbose_name='Σχολείο')
    fek = models.CharField(null=True, blank=True, max_length=30, verbose_name='ΦΕΚ Διορισμού')
    appointment_date = models.DateField(null=True, blank=True, verbose_name='Ημερομηνία Διορισμού')
    mobile = models.CharField(null=True, blank=True, max_length=25, verbose_name='Κινητό')
    mail = models.CharField(null=True, blank=True, max_length=100, verbose_name='E-mail')
    participates = models.BooleanField(default=True, verbose_name='Συμμετέχει στην αξιολόγηση')
    comments = models.TextField(null=True, blank=True, default='', max_length=200, verbose_name='Σχόλια')
    is_active = models.BooleanField(default=True, verbose_name='Ενεργός εκπαιδευτικός')

    def save(self, *args, **kwargs):
        # Ensure afm is 9 characters long
        if self.afm and len(self.afm) == 8:
            self.afm = self.afm.zfill(9)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Εκπαιδευτικός"
        verbose_name_plural = "Εκπαιδευτικοί"
        # constraints = [
        #     models.UniqueConstraint(fields=['afm', 'evaluation_year'], name='unique_teacher')
        # ]

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.specialty}"


class EvaluationStepType(models.Model):
    title = models.CharField(max_length=100, verbose_name='Βήμα Αξιολόγησης')

    class Meta:
        verbose_name = "Τύπος βήματος αξιολόγησης"
        verbose_name_plural = "Τύποι βημάτων αξιολόγησης"
        constraints = [
            models.UniqueConstraint(fields=['title'],
                                    name='unique_evaluation_step_type')
        ]

    def __str__(self):
        return self.title


def custom_documents_directory_path(instance, filename):
    pass
    file_extension = os.path.splitext(filename)[1][1:].lower()
    return f'documents/{instance.teacher.evaluation_year}/{slugify(str(instance.teacher))}/{slugify(str(instance.es_type))}.{file_extension}'


class EvaluationStep(models.Model):
    consultant = models.ForeignKey(User, null=False, on_delete=models.CASCADE,
                                   verbose_name='Σύμβουλος Εκπαίδευσης',
                                   related_name='consultant_evaluation_steps')
    teacher = models.ForeignKey(Teacher, null=False, on_delete=models.CASCADE, verbose_name='Εκπαιδευτικός',
                                related_name='teacher_evaluation_steps')
    es_type = models.ForeignKey(EvaluationStepType, null=False, on_delete=models.CASCADE,
                                verbose_name='Βήμα Αξιολόγησης')
    es_date = models.DateField(null=False, blank=False, verbose_name='Ημερομηνία')
    complete = models.BooleanField(default=False, verbose_name='Ολοκληρώθηκε')

    evaluation_document = models.FileField(null=True, blank=True, upload_to=custom_documents_directory_path,
                                           verbose_name='Αρχείο Αξιολόγησης')
    comments = models.TextField(null=True, blank=True, default='', max_length=200, verbose_name='Σχόλια')
    timestamp = models.DateTimeField(auto_now=True, verbose_name='Χρονική σήμανση')
    downloaded = models.BooleanField(default=False, verbose_name='Έγινε λήψη')
    approved = models.BooleanField(default=False, verbose_name='Εγκρίθηκε')
    to_review = models.BooleanField(default=False, verbose_name='Για αναθεώρηση')
    comments_from_director = models.TextField(null=True, blank=True, default='', max_length=200,
                                              verbose_name='Σχόλια Επόπτη Ποιότητας')

    class Meta:
        verbose_name = "Βήμα αξιολόγησης"
        verbose_name_plural = "Βήματα αξιολόγησης"
        constraints = [
            models.UniqueConstraint(fields=['consultant', 'teacher', 'es_type'], name='unique_evaluation_step')
        ]

    def delete(self, *args, **kwargs):
        try:
            if os.path.isfile(self.evaluation_document.path):
                os.remove(self.evaluation_document.path)
        except:
            print("File deletion error !!!")

        super(EvaluationStep, self).delete(*args, **kwargs)

    def __str__(self):
        return f"{self.consultant} {self.teacher} {self.es_type} {self.es_date}"


class TeacherAssignment(models.Model):
    teacher_last_name = models.CharField(null=True, blank=True, max_length=50, verbose_name='Επώνυμο εκπ/κού')
    teacher_first_name = models.CharField(null=True, blank=True, max_length=50, verbose_name='Όνομα εκπ/κού')
    teacher_afm = models.CharField(null=False, blank=False, max_length=9, verbose_name='ΑΦΜ εκπαιδευτικού')
    consultant_last_name = models.CharField(null=True, blank=True, max_length=50, verbose_name='Επώνυμο συμβούλου')
    consultant_first_name = models.CharField(null=True, blank=True, max_length=50, verbose_name='Όνομα συμβούλου')
    consultant_afm = models.CharField(null=False, blank=False, max_length=9, verbose_name='ΑΦΜ συμβούλου')
    loaded = models.BooleanField(default=False, verbose_name='Καταχωρήθηκε')
    comments = models.CharField(null=True, blank=True, max_length=300, verbose_name='Σχόλια')

    def save(self, *args, **kwargs):
        # Ensure teacher_afm and consultant_afm are 9 characters long
        if self.teacher_afm and len(self.teacher_afm) == 8:
            self.teacher_afm = self.teacher_afm.zfill(9)
        if self.consultant_afm and len(self.consultant_afm) == 8:
            self.consultant_afm = self.consultant_afm.zfill(9)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ανάθεση εκπαιδευτικού"
        verbose_name_plural = "Αναθέσεις εκπαιδευτικών"

    def __str__(self):
        return f"{self.teacher_afm} <-> {self.consultant_afm}"

# Override user display_name
# https://stackoverflow.com/questions/34214320/django-customize-the-user-models-return-field
def get_user_display(self):
    return f"{self.last_name} {self.first_name}"

User.add_to_class("__str__", get_user_display)


# Site configuration model
class SiteConfiguration(SingletonModel):
    show_office_days = models.BooleanField('Εμφάνιση ημερών γραφείου', default=False)
    email_host = models.CharField('Διακομιστής αλληλογραφίας', max_length=255, default='smtp.gmail.com',null=True, blank=True)
    email_tls = models.BooleanField('Χρήση TLS', default=True)
    email_port = models.IntegerField('Θύρα Διακομιστή αλληλογραφίας', default='587')
    email_username = models.CharField('Όνομα χρήστη αλληλογραφίας', max_length=50, default='username',null=True, blank=True)
    email_password = models.CharField('Κωδικός χρήστη αλληλογραφίας', max_length=50, default='password',null=True, blank=True)
    email_from = models.CharField('Email αποστολέα', max_length=50, default='', null=True, blank=True)
    recipient_list = models.CharField('Email παραληπτών (χωρισμένα με κόμμα)', max_length=255, default='',null=True, blank=True)

    def __str__(self):
        return "Παράμετροι εφαρμογής"

    class Meta:
        verbose_name = "Παράμετροι εφαρμογής"
