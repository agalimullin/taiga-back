# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-09 18:36
from __future__ import unicode_literals

import datetime
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import taiga.base.db.models.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0005_project_burnup_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='BurnupChart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', taiga.base.db.models.fields.json.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='data')),
                ('created_date', models.DateField(default=datetime.date.today, verbose_name='created date')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='burnup_chart_stats', to='projects.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'burnup chart',
                'verbose_name_plural': 'burnup charts',
                'ordering': ['created_date', 'project_id'],
            },
        ),
        migrations.CreateModel(
            name='CumulativeFlowDiagram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', taiga.base.db.models.fields.json.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='data')),
                ('created_date', models.DateField(default=datetime.date.today, verbose_name='created date')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cumulative_flow_diagram_stats', to='projects.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'cumulative flow diagram',
                'verbose_name_plural': 'cumulative flow diagrams',
                'ordering': ['created_date', 'project_id'],
            },
        ),
        migrations.CreateModel(
            name='VelocityChart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_sprints_velocities', taiga.base.db.models.fields.json.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='project sprints velocities')),
                ('created_date', models.DateField(default=datetime.date.today, verbose_name='created date')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='velocity_chart_stats', to='projects.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'velocity chart',
                'verbose_name_plural': 'velocity charts',
                'ordering': ['created_date', 'project_id'],
            },
        ),
    ]
