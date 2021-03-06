# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FeedbackEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=256, verbose_name='full name')),
                ('email', models.EmailField(max_length=255, verbose_name='email address')),
                ('comment', models.TextField(verbose_name='comment')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='created date')),
            ],
            options={
                'verbose_name': 'feedback entry',
                'verbose_name_plural': 'feedback entries',
                'ordering': ['-created_date', 'id'],
            },
        ),
    ]
