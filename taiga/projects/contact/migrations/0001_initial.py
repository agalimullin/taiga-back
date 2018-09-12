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
            name='ContactEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(verbose_name='comment')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='created date')),
            ],
            options={
                'verbose_name': 'contact entry',
                'verbose_name_plural': 'contact entries',
                'ordering': ['-created_date', 'id'],
            },
        ),
    ]
