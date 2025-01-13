# Generated by Django 5.1.3 on 2025-01-08 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metakinhseis', '0006_metakinhsh_is_evaluation'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultant',
            name='am',
            field=models.CharField(max_length=10, null=True, verbose_name='Αριθμός μητρώου'),
        ),
        migrations.AddField(
            model_name='consultant',
            name='iban',
            field=models.CharField(max_length=50, null=True, verbose_name='IBAN'),
        ),
        migrations.AlterField(
            model_name='metakinhsh',
            name='is_evaluation',
            field=models.BooleanField(default=False, verbose_name='Μετακ.αξιολόγησης'),
        ),
    ]