# Generated by Django 5.1.3 on 2025-01-03 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metakinhseis', '0005_alter_consultant_options_alter_metakinhsh_km'),
    ]

    operations = [
        migrations.AddField(
            model_name='metakinhsh',
            name='is_evaluation',
            field=models.BooleanField(default=False, verbose_name='Μετακίνηση για αξιολόγηση'),
        ),
    ]