# Generated by Django 5.1.3 on 2025-03-06 11:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('symvouloi', '0009_teacher_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluationData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consultant_a1', models.TextField(blank=True, max_length=100, null=True, verbose_name='Αξιολογητής A1')),
                ('a1_result', models.TextField(blank=True, max_length=100, null=True, verbose_name='Αποτέλεσμα Α1')),
                ('a1_evaluation_date', models.DateTimeField(blank=True, null=True, verbose_name='Ημ/νία - ώρα Αξιολόγησης A1')),
                ('consultant_a2', models.TextField(blank=True, max_length=100, null=True, verbose_name='Αξιολογητής A2')),
                ('a2_result', models.TextField(blank=True, max_length=100, null=True, verbose_name='Αποτέλεσμα Α2')),
                ('a2_evaluation_date', models.DateTimeField(blank=True, null=True, verbose_name='Ημ/νία - ώρα Αξιολόγησης A2')),
                ('consultant_b', models.TextField(blank=True, max_length=100, null=True, verbose_name='Αξιολογητής B')),
                ('b_result', models.TextField(blank=True, max_length=100, null=True, verbose_name='Αποτέλεσμα B')),
                ('b_evaluation_date', models.DateTimeField(blank=True, null=True, verbose_name='Ημ/νία - ώρα Αξιολόγησης Β')),
                ('permanent', models.BooleanField(default=False, verbose_name='Μονιμοποίηση')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='symvouloi.teacher', verbose_name='Εκπαιδευτικός')),
            ],
            options={
                'verbose_name': 'Αξιολογήση',
                'verbose_name_plural': 'Αξιολογήσεις',
            },
        ),
    ]
