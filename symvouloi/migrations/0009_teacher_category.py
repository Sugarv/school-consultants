# Generated by Django 5.1.3 on 2025-02-26 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('symvouloi', '0008_evaluationstep_linked_metakinhsh_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='category',
            field=models.CharField(blank=True, choices=[('A', 'A'), ('A1', 'A1'), ('A2', 'A2'), ('B', 'B')], max_length=5, null=True, verbose_name='Κατηγορία αξιολόγησης'),
        ),
    ]
