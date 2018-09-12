# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-08-21 19:39
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.auth.models
import django.contrib.postgres.fields
import django.core.serializers.json
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import re
import taiga.base.db.models.fields.json
import taiga.base.utils.colors
import taiga.users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('uuid', models.CharField(default=taiga.users.models.get_default_uuid, editable=False, max_length=32, unique=True)),
                ('username', models.CharField(help_text='Required. 30 characters or fewer. Letters, numbers and /./-/_ characters', max_length=255, unique=True, validators=[django.core.validators.RegexValidator(re.compile('^[\\w.-]+$', 32), 'Enter a valid username.', 'invalid')], verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=255, unique=True, verbose_name='email address')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('full_name', models.CharField(blank=True, max_length=256, verbose_name='full name')),
                ('color', models.CharField(blank=True, default=taiga.base.utils.colors.generate_random_hex_color, max_length=9, verbose_name='color')),
                ('bio', models.TextField(blank=True, default='', verbose_name='biography')),
                ('photo', models.FileField(blank=True, max_length=500, null=True, upload_to=taiga.users.models.get_user_file_path, verbose_name='photo')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('accepted_terms', models.BooleanField(default=True, verbose_name='accepted terms')),
                ('read_new_terms', models.BooleanField(default=False, verbose_name='new terms read')),
                ('lang', models.CharField(blank=True, default='', max_length=20, null=True, verbose_name='default language')),
                ('theme', models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='default theme')),
                ('timezone', models.CharField(blank=True, default='', max_length=20, null=True, verbose_name='default timezone')),
                ('colorize_tags', models.BooleanField(default=False, verbose_name='colorize tags')),
                ('token', models.CharField(blank=True, default=None, max_length=200, null=True, verbose_name='token')),
                ('email_token', models.CharField(blank=True, default=None, max_length=200, null=True, verbose_name='email token')),
                ('new_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='new email address')),
                ('is_system', models.BooleanField(default=False)),
                ('max_private_projects', models.IntegerField(blank=True, default=None, null=True, verbose_name='max number of owned private projects')),
                ('max_public_projects', models.IntegerField(blank=True, default=None, null=True, verbose_name='max number of owned public projects')),
                ('max_memberships_private_projects', models.IntegerField(blank=True, default=None, null=True, verbose_name='max number of memberships for each owned private project')),
                ('max_memberships_public_projects', models.IntegerField(blank=True, default=None, null=True, verbose_name='max number of memberships for each owned public project')),
                ('projects_activity', taiga.base.db.models.fields.json.JSONField(blank=True, default=None, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'ordering': ['username'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='AuthData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField()),
                ('value', models.CharField(max_length=300)),
                ('extra', taiga.base.db.models.fields.json.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_data', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('slug', models.SlugField(blank=True, max_length=250, verbose_name='slug')),
                ('permissions', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(choices=[('view_project', 'View project'), ('view_milestones', 'View milestones'), ('add_milestone', 'Add milestone'), ('modify_milestone', 'Modify milestone'), ('delete_milestone', 'Delete milestone'), ('view_epics', 'View epic'), ('add_epic', 'Add epic'), ('modify_epic', 'Modify epic'), ('comment_epic', 'Comment epic'), ('delete_epic', 'Delete epic'), ('view_us', 'View user story'), ('add_us', 'Add user story'), ('modify_us', 'Modify user story'), ('comment_us', 'Comment user story'), ('delete_us', 'Delete user story'), ('view_tasks', 'View tasks'), ('add_task', 'Add task'), ('modify_task', 'Modify task'), ('comment_task', 'Comment task'), ('delete_task', 'Delete task'), ('view_issues', 'View issues'), ('add_issue', 'Add issue'), ('modify_issue', 'Modify issue'), ('comment_issue', 'Comment issue'), ('delete_issue', 'Delete issue'), ('view_wiki_pages', 'View wiki pages'), ('add_wiki_page', 'Add wiki page'), ('modify_wiki_page', 'Modify wiki page'), ('comment_wiki_page', 'Comment wiki page'), ('delete_wiki_page', 'Delete wiki page'), ('view_wiki_links', 'View wiki links'), ('add_wiki_link', 'Add wiki link'), ('modify_wiki_link', 'Modify wiki link'), ('delete_wiki_link', 'Delete wiki link')]), blank=True, default=[], null=True, size=None, verbose_name='permissions')),
                ('order', models.IntegerField(default=10, verbose_name='order')),
                ('computable', models.BooleanField(default=True)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='projects.Project', verbose_name='project')),
            ],
            options={
                'verbose_name': 'role',
                'verbose_name_plural': 'roles',
                'ordering': ['order', 'slug'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='role',
            unique_together=set([('slug', 'project')]),
        ),
        migrations.AlterUniqueTogether(
            name='authdata',
            unique_together=set([('key', 'value')]),
        ),
    ]
