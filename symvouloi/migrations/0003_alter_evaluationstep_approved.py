# Generated by Django 5.1.3 on 2024-12-20 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('symvouloi', '0002_alter_evaluationstep_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluationstep',
            name='approved',
            field=models.BooleanField(default=False, verbose_name='Εγκρίθηκε'),
        ),
    ]