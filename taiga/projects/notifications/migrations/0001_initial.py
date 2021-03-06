# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taiga.projects.history.choices
import taiga.projects.notifications.choices


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryChangeNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(editable=False, max_length=255)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='created date time')),
                ('updated_datetime', models.DateTimeField(auto_now_add=True, verbose_name='updated date time')),
                ('history_type', models.SmallIntegerField(choices=[(taiga.projects.history.choices.HistoryType(1), 'Change'), (taiga.projects.history.choices.HistoryType(2), 'Create'), (taiga.projects.history.choices.HistoryType(3), 'Delete')])),
            ],
        ),
        migrations.CreateModel(
            name='NotifyPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notify_level', models.SmallIntegerField(choices=[(taiga.projects.notifications.choices.NotifyLevel(1), 'Involved'), (taiga.projects.notifications.choices.NotifyLevel(2), 'All'), (taiga.projects.notifications.choices.NotifyLevel(3), 'None')])),
                ('live_notify_level', models.SmallIntegerField(choices=[(taiga.projects.notifications.choices.NotifyLevel(1), 'Involved'), (taiga.projects.notifications.choices.NotifyLevel(2), 'All'), (taiga.projects.notifications.choices.NotifyLevel(3), 'None')], default=taiga.projects.notifications.choices.NotifyLevel(1))),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField()),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Watched',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='created date')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Watched',
                'verbose_name_plural': 'Watched',
            },
        ),
    ]
