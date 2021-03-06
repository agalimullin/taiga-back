# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taiga.projects.attachments.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(verbose_name='object id')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('name', models.CharField(blank=True, default='', max_length=500)),
                ('size', models.IntegerField(blank=True, default=None, editable=False, null=True)),
                ('attached_file', models.FileField(blank=True, max_length=500, null=True, upload_to=taiga.projects.attachments.models.get_attachment_file_path, verbose_name='attached file')),
                ('sha1', models.CharField(blank=True, default='', max_length=40, verbose_name='sha1')),
                ('is_deprecated', models.BooleanField(default=False, verbose_name='is deprecated')),
                ('from_comment', models.BooleanField(default=False, verbose_name='from comment')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('order', models.IntegerField(default=0, verbose_name='order')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', verbose_name='content type')),
            ],
            options={
                'verbose_name': 'attachment',
                'verbose_name_plural': 'attachments',
                'ordering': ['project', 'created_date', 'id'],
                'permissions': (('view_attachment', 'Can view attachment'),),
            },
        ),
    ]
