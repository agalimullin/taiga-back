# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('likes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='like',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
        migrations.AlterUniqueTogether(
            name='like',
            unique_together=set([('content_type', 'object_id', 'user')]),
        ),
    ]
