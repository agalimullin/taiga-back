# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
        ('epics', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userstories', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='relateduserstory',
            name='user_story',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userstories.UserStory'),
        ),
        migrations.AddField(
            model_name='epic',
            name='assigned_to',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='epics_assigned_to_me', to=settings.AUTH_USER_MODEL, verbose_name='assigned to'),
        ),
        migrations.AddField(
            model_name='epic',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_epics', to=settings.AUTH_USER_MODEL, verbose_name='owner'),
        ),
        migrations.AddField(
            model_name='epic',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='epics', to='projects.Project', verbose_name='project'),
        ),
        migrations.AddField(
            model_name='epic',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='epics', to='projects.EpicStatus', verbose_name='status'),
        ),
        migrations.AddField(
            model_name='epic',
            name='user_stories',
            field=models.ManyToManyField(related_name='epics', through='epics.RelatedUserStory', to='userstories.UserStory', verbose_name='user stories'),
        ),
        migrations.AlterUniqueTogether(
            name='relateduserstory',
            unique_together=set([('user_story', 'epic')]),
        ),
    ]
