# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import taiga.base.db.models.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Webhook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250, verbose_name='name')),
                ('url', models.URLField(verbose_name='URL')),
                ('key', models.TextField(verbose_name='secret key')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='projects.Project')),
            ],
            options={
                'ordering': ['name', '-id'],
            },
        ),
        migrations.CreateModel(
            name='WebhookLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(verbose_name='URL')),
                ('status', models.IntegerField(verbose_name='status code')),
                ('request_data', taiga.base.db.models.fields.json.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='request data')),
                ('request_headers', taiga.base.db.models.fields.json.JSONField(default={}, encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='request headers')),
                ('response_data', models.TextField(verbose_name='response data')),
                ('response_headers', taiga.base.db.models.fields.json.JSONField(default={}, encoder=django.core.serializers.json.DjangoJSONEncoder, verbose_name='response headers')),
                ('duration', models.FloatField(default=0, verbose_name='duration')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('webhook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='webhooks.Webhook')),
            ],
            options={
                'ordering': ['-created', '-id'],
            },
        ),
    ]
