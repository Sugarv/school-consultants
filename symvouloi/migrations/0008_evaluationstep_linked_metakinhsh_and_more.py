# Generated by Django 5.1.3 on 2025-02-13 07:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metakinhseis', '0010_alter_officeschedule_options_and_more'),
        ('symvouloi', '0007_delete_siteconfiguration'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluationstep',
            name='linked_metakinhsh',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='metakinhseis.metakinhsh', verbose_name='Σχετική Μετακίνηση'),
        ),
        migrations.AlterField(
            model_name='evaluationstep',
            name='comments',
            field=models.TextField(blank=True, default='', max_length=2000, null=True, verbose_name='Σχόλια'),
        ),
    ]
