# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taiga.base.db.models.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0002_auto_20180821_2239'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Timeline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('namespace', models.CharField(db_index=True, default='default', max_length=250)),
                ('event_type', models.CharField(db_index=True, max_length=250)),
                ('data', taiga.base.db.models.fields.json.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_type_timelines', to='contenttypes.ContentType')),
                ('data_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_timelines', to='contenttypes.ContentType')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='projects.Project')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='timeline',
            index_together=set([('namespace', 'created'), ('content_type', 'object_id', 'namespace')]),
        ),
    ]
