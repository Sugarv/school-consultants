# Generated by Django 5.1.3 on 2024-12-04 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('symvouloi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluationstep',
            name='timestamp',
            field=models.DateTimeField(auto_now=True, verbose_name='Χρονική σήμανση'),
        ),
    ]
