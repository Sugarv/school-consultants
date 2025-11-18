# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import os
import random
from django.db import models
from django.conf import settings
# from django.core.validators import RegexValidator
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User


def custom_documents_directory_path(instance, filename):
    file_extension = os.path.splitext(filename)[1][1:].lower()
    return f'documents/{instance.consultant.username}-{instance.date_from}_{random.randint(0,1000)}.{file_extension}'

class Metakinhsh(models.Model):
  consultant = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, verbose_name='Χρήστης', null=True)
  metak_from = models.CharField('Από', max_length=100)
  metak_to = models.CharField('Προορισμός', max_length=100)
  date_from = models.DateField('Ημ/νία Από')
  date_to = models.DateField('Ημ/νία Έως',null=True)
  km = models.FloatField('Χιλιόμετρα', help_text="Παρακαλώ εισάγετε την απόσταση από το Α στο Β, όχι όλης της διαδρομής")
  egkrish = models.BooleanField('Έγκριση', default=False)
  pragmat = models.BooleanField('Πραγματοποιήθηκε', default=False)
  aitiologia = models.TextField('Αιτιολογία', max_length=150)
  handler = models.CharField('Χειριστής',max_length=80,default=None,blank=True,null=True,choices=(
      ('Επόπτης', 'Επόπτης'),('Οικονομικό', 'Οικονομικό')))
  to_pay = models.BooleanField(default=False, verbose_name='Για πληρωμή (>50 χλμ)')
  amount1 = models.FloatField(default=0.0, verbose_name='Ποσό για μετακίνηση')
  away = models.BooleanField(default=False, verbose_name='Εκτός έδρας')
  amount2 = models.FloatField(default=0.0, verbose_name='Ποσό για ημ. αποζημ.')
  tickets = models.BooleanField(default=False, verbose_name='Εισιτήρια')
  amount3 = models.FloatField(default=0.0, verbose_name='Ποσό για εισιτήρια')
  stay = models.BooleanField(default=False, verbose_name='Διαμονή')
  amount4 = models.FloatField(default=0.0, verbose_name='Ποσό για διαμονή')
  file = models.FileField(default='', upload_to=custom_documents_directory_path, verbose_name='Αρχείο', null=True, blank=True)
  uploaded_at = models.DateTimeField(null=True, blank=True, verbose_name='ΧΣΜ')
  special = models.BooleanField(default=False, verbose_name='Ειδική περίπτωση')
  is_evaluation = models.BooleanField(default=False, verbose_name='Μετακ.αξιολόγησης')
  dyee = models.BooleanField(default=False, verbose_name='Προωθήθηκε στη ΔΥΕΕ')
  school_year = models.CharField('Σχολικό έτος', max_length=20, null=True, blank=True)
  updated_at = models.DateTimeField(auto_now=True, verbose_name='Τελευταία ενημέρωση')
  
  class Meta:
    verbose_name = 'Μετακίνηση'
    verbose_name_plural = 'Μετακινήσεις'

  def __str__(self):
    return f'{self.consultant.last_name} -> {self.metak_to} @ {self.date_from}'
  
  def get_absolute_url(self): # new
    return reverse('metakinhsh_list')#, args=[str(self.id)])
  
  def save(self, *args, **kwargs):
    # Automatically set 'handler' to 'Επόπτης' if 'km' is less than 50
    if self.km is not None and self.km < 50:
        self.handler = 'Επόπτης'
    else:
        self.handler = 'Οικονομικό'
    super().save(*args, **kwargs)

# Use signals to send_mail when a new object is created in Metakinhsh
# when _skip_email is set, no email is sent
@receiver(post_save, sender=Metakinhsh)
def send_email(sender, instance, created, **kwargs):
    if created and not getattr(instance, "_skip_email", False):
        fname = instance.consultant.first_name + ' ' + instance.consultant.last_name
        formatted_date = instance.date_from.strftime("%d/%m/%Y")
        subject = 'Νέα Μετακίνηση'
        message = f'<h3>Εισαγωγή νέας μετακίνησης</h3><br>Σύμβουλος εκπαίδευσης: <b>{fname}</b><br>Ημερομηνία: <b>{formatted_date}</b><br>\
          Προορισμός: <b>{instance.metak_to}</b><br>Αιτιολογία: <b>{instance.aitiologia}</b>'
        # check if debug. If yes, print message, else send the email
        if settings.DEBUG == True:
          print("Email text:")
          print(message)
        else:
          from_email = settings.DEFAULT_FROM_EMAIL
          recipient_list = settings.RECIPIENT_LIST
          send_mail(subject, message, from_email, recipient_list, html_message=message)


# Supportive Model for extra consultant data (mainly for the documents)
class Consultant(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  klados = models.CharField('Ειδικότητα', max_length=80, null=True, blank=True)
  enothta = models.CharField('Ενότητα', max_length=80, null=True, blank=True)
  iban = models.CharField('IBAN', max_length=50, null=True, blank=True)
  am = models.CharField('Αριθμός μητρώου', max_length=10, null=True, blank=True)

  class Meta:
    verbose_name = 'Σύμβουλος'
    verbose_name_plural = 'Σύμβουλοι'

  def __str__(self):
    return f'{self.user.last_name} {self.user.first_name}'


class OfficeSchedule(models.Model):
    consultant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Χρήστης',
        null=True
    )
    month = models.CharField('Μήνας',max_length=20, null=True, blank=True)
    days_in_office = models.JSONField('Ημέρες γραφείου',default=list)

    def __str__(self):
        return f"{self.consultant} - {self.month}"
    
    class Meta:
      verbose_name = 'Ημέρα γραφείου'
      verbose_name_plural = 'Ημέρες γραφείου'