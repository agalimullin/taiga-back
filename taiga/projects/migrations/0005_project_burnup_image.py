# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-09 18:26
from __future__ import unicode_literals

from django.db import migrations, models
import taiga.projects.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_auto_20180825_2351'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='burnup_image',
            field=models.FileField(blank=True, max_length=500, null=True, upload_to=taiga.projects.models.get_project_file_path, verbose_name='burnup image'),
        ),
    ]
