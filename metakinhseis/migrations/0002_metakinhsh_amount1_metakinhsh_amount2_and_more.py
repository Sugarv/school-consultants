# Generated by Django 5.1.3 on 2024-12-10 09:37

import metakinhseis.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metakinhseis', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='metakinhsh',
            name='amount1',
            field=models.FloatField(default=0.0, verbose_name='Ποσό για μετακίνηση'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='amount2',
            field=models.FloatField(default=0.0, verbose_name='Ποσό για ημ. αποζημ.'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='amount3',
            field=models.FloatField(default=0.0, verbose_name='Ποσό για εισιτήρια'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='amount4',
            field=models.FloatField(default=0.0, verbose_name='Ποσό για διαμονή'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='away',
            field=models.BooleanField(default=False, verbose_name='Εκτός έδρας'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='file',
            field=models.FileField(default='', upload_to=metakinhseis.models.custom_documents_directory_path, verbose_name='Αρχείο'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='special',
            field=models.BooleanField(default=False, verbose_name='Ειδική περίπτωση'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='stay',
            field=models.BooleanField(default=False, verbose_name='Διαμονή'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='tickets',
            field=models.BooleanField(default=False, verbose_name='Εισιτήρια'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='to_pay',
            field=models.BooleanField(default=False, verbose_name='Για πληρωμή (>50 χλμ)'),
        ),
        migrations.AddField(
            model_name='metakinhsh',
            name='uploaded_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='ΧΣΜ'),
        ),
    ]