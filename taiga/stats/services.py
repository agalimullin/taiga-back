# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Taiga Agile LLC <support@taiga.io>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import base64

import os
import io
import random
import string

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.images import ImageFile
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone

from datetime import timedelta, date, datetime
from collections import OrderedDict

from matplotlib.dates import WeekdayLocator, MONDAY, DateFormatter

from taiga.projects.services import get_stats_for_project
from . import models
from taiga.projects.models import Project, UserStoryStatus
from taiga.projects.milestones.models import Milestone
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.custom_attributes.models import UserStoryCustomAttribute
from taiga.projects.custom_attributes.models import UserStoryCustomAttributesValues

from taiga.users.models import User
from taiga.projects.history.models import HistoryEntry

import re
import sys
import time
import numpy
import matplotlib
import xlwt


matplotlib.use('Agg')
import matplotlib.pyplot as plt


###########################################################################
# Public Stats
###########################################################################


def get_users_public_stats():
    model = get_user_model()
    queryset = model.objects.filter(is_active=True, is_system=False)
    stats = OrderedDict()

    today = timezone.now()
    yesterday = today - timedelta(days=1)
    seven_days_ago = yesterday - timedelta(days=7)
    a_year_ago = today - timedelta(days=365)

    stats["total"] = queryset.count()
    stats["today"] = queryset.filter(date_joined__year=today.year,
                                     date_joined__month=today.month,
                                     date_joined__day=today.day).count()
    stats["average_last_seven_days"] = (queryset.filter(date_joined__range=(seven_days_ago, yesterday))
                                        .count()) / 7
    stats["average_last_five_working_days"] = (queryset.filter(date_joined__range=(seven_days_ago, yesterday))
                                               .exclude(Q(date_joined__week_day=1) |
                                                        Q(date_joined__week_day=7))
                                               .count()) / 5

    # Graph: users last year
    # increments ->
    #   SELECT date_trunc('week', "filtered_users"."date_joined") AS "week",
    #          count(*)
    #     FROM (SELECT *
    #             FROM "users_user"
    #            WHERE "users_user"."is_active" = TRUE
    #              AND "users_user"."is_system" = FALSE
    #              AND "users_user"."date_joined" >= %s) AS "filtered_users"
    # GROUP BY "week"
    # ORDER BY "week";
    increments = (queryset.filter(date_joined__gte=a_year_ago)
                  .extra({"week": "date_trunc('week', date_joined)"})
                  .values("week")
                  .order_by("week")
                  .annotate(count=Count("id")))

    counts_last_year_per_week = OrderedDict()
    sumatory = queryset.filter(date_joined__lt=increments[0]["week"]).count()
    for inc in increments:
        sumatory += inc["count"]
        counts_last_year_per_week[str(inc["week"].date())] = sumatory

    stats["counts_last_year_per_week"] = counts_last_year_per_week

    return stats


def get_projects_public_stats():
    model = apps.get_model("projects", "Project")
    queryset = model.objects.all()
    stats = OrderedDict()

    today = timezone.now()
    yesterday = today - timedelta(days=1)
    seven_days_ago = yesterday - timedelta(days=7)

    stats["total"] = queryset.count()
    stats["today"] = queryset.filter(created_date__year=today.year,
                                     created_date__month=today.month,
                                     created_date__day=today.day).count()
    stats["average_last_seven_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                        .count()) / 7
    stats["average_last_five_working_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                               .exclude(Q(created_date__week_day=1) |
                                                        Q(created_date__week_day=7))
                                               .count()) / 5

    stats["total_with_backlog"] = (queryset.filter(is_backlog_activated=True,
                                                   is_kanban_activated=False)
                                   .count())
    stats["percent_with_backlog"] = stats["total_with_backlog"] * 100 / stats["total"]

    stats["total_with_kanban"] = (queryset.filter(is_backlog_activated=False,
                                                  is_kanban_activated=True)
                                  .count())
    stats["percent_with_kanban"] = stats["total_with_kanban"] * 100 / stats["total"]

    stats["total_with_backlog_and_kanban"] = (queryset.filter(is_backlog_activated=True,
                                                              is_kanban_activated=True)
                                              .count())
    stats["percent_with_backlog_and_kanban"] = stats["total_with_backlog_and_kanban"] * 100 / stats["total"]

    return stats


def get_user_stories_public_stats():
    model = apps.get_model("userstories", "UserStory")
    queryset = model.objects.all()
    stats = OrderedDict()

    today = timezone.now()
    yesterday = today - timedelta(days=1)
    seven_days_ago = yesterday - timedelta(days=7)

    stats["total"] = queryset.count()
    stats["today"] = queryset.filter(created_date__year=today.year,
                                     created_date__month=today.month,
                                     created_date__day=today.day).count()
    stats["average_last_seven_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                        .count()) / 7
    stats["average_last_five_working_days"] = (queryset.filter(created_date__range=(seven_days_ago, yesterday))
                                               .exclude(Q(created_date__week_day=1) |
                                                        Q(created_date__week_day=7))
                                               .count()) / 5

    return stats


###########################################################################
# Discover Stats
###########################################################################


def get_projects_discover_stats(user=None):
    model = apps.get_model("projects", "Project")
    queryset = model.objects.all()
    stats = OrderedDict()

    # Get Public (visible) projects
    queryset = queryset.filter(Q(is_private=False) |
                               Q(is_private=True, anon_permissions__contains=["view_project"]))

    stats["total"] = queryset.count()

    return stats


###########################################################################
# Agile Stats Updating
###########################################################################


# функция сбора данных проекта для обратной диаграммы выгорания
def add_new_burnup_project_data(project):
    # burnup объект проекта за предыдущий день
    previous_db_object = None
    # если burnup объект проекта за предыдущий день существует
    try:
        previous_db_object = models.BurnupChart.objects.get(created_date=date.today() - timedelta(days=1), project=project)
    except ObjectDoesNotExist:
        previous_db_object = None
    # если burnup объект проекта за сегодняшний день уже существует, то удаляем
    try:
        existed_object = models.BurnupChart.objects.get(created_date=date.today(), project=project)
        existed_object.delete()
    except ObjectDoesNotExist:
        pass
    # целевые очки проекта
    total_story_points = getattr(project, 'total_story_points')
    # спринты проекта
    project_milestones = Milestone.objects.filter(project=project)

    # конечный лист для записи в БД
    data = []

    # если у проекта есть спринты
    if project_milestones:
        # счётчик закрытых очков
        previous_closed = 0
        # пробегаемся по спринтам
        for i in range(len(project_milestones)):
            sprint_data = {}

            if previous_db_object:
                # проверяем, входит ли сегодняшняя дата в диапазон спринта
                if getattr(project_milestones[i], 'estimated_start') < date.today() < getattr(project_milestones[i], 'estimated_finish'):
                    sprint_data['target_project_points'] = total_story_points
                elif 0 <= i < len(getattr(previous_db_object, 'data')) and 'target_project_points' in getattr(previous_db_object, 'data')[i]:
                    sprint_data['target_project_points'] = getattr(previous_db_object, 'data')[i]['target_project_points']
                else:
                    sprint_data['target_project_points'] = total_story_points
            else:
                sprint_data['target_project_points'] = total_story_points

            if getattr(project_milestones[i], 'closed_points'):
                closed_points = sum(getattr(project_milestones[i], 'closed_points').values())
            else:
                closed_points = 0
            closed_points += previous_closed
            sprint_data['completed_points'] = closed_points
            sprint_data['sprint_date'] = getattr(project_milestones[i], 'estimated_start')
            data.append(sprint_data)
            previous_closed += closed_points

    b = models.BurnupChart()
    b.project = project
    b.data = data
    b.save()
    print('Added new burnup data of project_' + str(getattr(project, 'id')))


# функция сбора данных проекта для диаграммы совокупного потока
def add_new_cumulative_flow_project_data(project):
    # если burnup объект проекта за сегодняшний день уже существует, то удаляем
    try:
        existed_object = models.CumulativeFlowDiagram.objects.get(created_date=date.today(), project=project)
        existed_object.delete()
    except ObjectDoesNotExist:
        pass
    try:
        previous_day_raw = models.CumulativeFlowDiagram.objects.get(created_date=date.today() - timedelta(days=1), project=project)
        previous_day_data = getattr(previous_day_raw, 'data')
    except ObjectDoesNotExist:
        previous_day_data = None
    uss = UserStory.objects.filter(project=project)
    uss_statuses_queryset = UserStoryStatus.objects.filter(project=project)
    status_ids, status_names = uss_statuses_queryset.values_list('id', flat=True)[
                               ::-1], uss_statuses_queryset.values_list('name', flat=True)[::-1]
    us_by_status = {status_id: [] for status_id in status_ids}
    for us in uss:
        us_by_status[getattr(us, 'status_id')].append(us)
    data = dict()
    data['date'] = str(date.today())
    data['annotation'] = 'NONE'
    data['annotation_layer'] = 0
    data['uss_counts'] = []
    for status_id in status_ids:
        no_uss = len(us_by_status[status_id])
        data['uss_counts'].append(no_uss)
    data['uss_statuses_names'] = status_names

    c = models.CumulativeFlowDiagram()
    c.project = project
    if previous_day_data is not None:
        previous_day_data.append(data)
        c.data = previous_day_data
    else:
        c.data = [data]
    c.save()
    print('Added new cfd of project_' + str(getattr(project, 'id')))


# функция сбора данных проекта для диаграммы скорости
def add_new_velocity_project_data(project):
    try:
        existed_object = models.VelocityChart.objects.get(created_date=date.today(), project=project)
        existed_object.delete()
    except ObjectDoesNotExist:
        pass
    v = models.VelocityChart()
    v.project = project
    if Milestone.objects.filter(project=project).exists():
        project_milestones = Milestone.objects.filter(project=project)
        velocities = []
        for milestone in project_milestones:
            milestone_data = dict()
            milestone_data['id'] = getattr(milestone, 'id')
            milestone_data['name'] = getattr(milestone, 'name')
            if getattr(milestone, 'closed_points'):
                milestone_data['closed_points'] = sum(getattr(milestone, 'closed_points').values())
            else:
                milestone_data['closed_points'] = 0
            milestone_data['total_points'] = sum(milestone.total_points.values())
            velocities.append(milestone_data)
        v.project_sprints_velocities = velocities
    else:
        v.project_sprints_velocities = {}
    v.save()
    print('Added new velocity data of project_' + str(getattr(project, 'id')))


# функция сбора текущих данных по проекту для дальнейшего построения всех диаграмм
def generate_stats(project):
    add_new_burnup_project_data(project)
    add_new_cumulative_flow_project_data(project)
    add_new_velocity_project_data(project)


###########################################################################
# Agile Stats Charts Generating
###########################################################################


# функция генерации обратной диаграммы выгорания проекта
def burnup_gen(project):
    try:
        burnup_data = models.BurnupChart.objects.get(project=project, created_date=date.today())
        fig, ax = plt.subplots()

        fig.suptitle("Burnup chart of {:s}".format(getattr(project, 'name')))

        sprints_days = [d['sprint_date'] for d in getattr(burnup_data, 'data') if 'sprint_date' in d]
        completed_points = [d['completed_points'] for d in getattr(burnup_data, 'data') if 'completed_points' in d]
        target_project_points = [d['target_project_points'] for d in getattr(burnup_data, 'data') if 'target_project_points' in d]
        # добавляем на график линии с target_project_points, completed_points
        ax.plot(sprints_days, target_project_points, 'bs-')
        ax.plot(sprints_days, completed_points, 'rs-')

        # подписываем ось Y
        plt.ylabel('Points')
        # добавляем сетку на график
        plt.grid()
        # поворачиваем и устанавливаем подписи точек на оси X
        plt.xticks(rotation=45)

        # добавляем легенду
        plt.plot(sprints_days, target_project_points, '-b',
                 label='Target project points')
        plt.plot(sprints_days, completed_points, '-r',
                 label='Completed points')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        # увеличиваем разрешение графика
        fig.set_size_inches(21.5, 10.5)

        # подписываем каждую точку графика
        for X, Y in zip(sprints_days, completed_points):
            # если есть координата Y (completed sprint points)
            if Y:
                ax.annotate('{}'.format(Y), xy=(X, Y), xytext=(-5, 5), ha='right',
                            textcoords='offset points')

        # Generation date string
        date_now = time.strftime("%Y-%m-%d %H:%M:%S")
        date_str = "Generated at {:s}".format(date_now)
        fig.text(0.015, 0.015, date_str)

        figure = io.BytesIO()
        plt.savefig(figure, format="png")
        content_file = ImageFile(figure)
        random_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        project.burnup_image.save(random_name + '.png', content_file)
        project.save(update_fields=["burnup_image"])

        plt.close(fig)
        plt.gcf().clear()
        print('Generated burnup png of project_' + str(getattr(project, 'id')))
    except ObjectDoesNotExist:
        return None


# функция генерации диаграммы совокупного потока проекта
def cumulative_flow_gen(project):
    try:
        cumulative_flow_data = models.CumulativeFlowDiagram.objects.get(project=project, created_date=date.today())
        processed_data = []
        # ============= processing ===============
        for i in range(0, len(getattr(cumulative_flow_data, 'data')[0]) - 2):
            processed_data.append([])
        for i in range(0, len(getattr(cumulative_flow_data, 'data')[0]['uss_counts']) + 1):
            processed_data.append([])
        for dict in getattr(cumulative_flow_data, 'data'):
            processed_data[0].append(datetime.strptime(dict['date'] + ' 00:00', "%Y-%m-%d %H:%M"))
            processed_data[1].append(dict['annotation'])
            processed_data[2].append(dict['annotation_layer'])
            i = 3
            for count in dict['uss_counts']:
                processed_data[i].append(count)
                i += 1
        # ========================================

        dates = processed_data[0]
        annotations = processed_data[1]
        annotation_layer = processed_data[2]
        data = processed_data[3:]

        uss_statuses_queryset = UserStoryStatus.objects.filter(project=project)
        status_ids, status_names = uss_statuses_queryset.values_list('id', flat=True)[
                                   ::-1], uss_statuses_queryset.values_list('name', flat=True)[::-1]
        if status_ids:
            selected_sids = status_ids
        else:
            selected_sids = None

        selected_snames = []
        selected_data = []
        for sid in selected_sids:
            try:
                idx = status_ids.index(sid)
            except ValueError:
                print("Selected US status ID {:d} not found for project {:s}!".format(sid, project.name))
                return 1
            selected_snames.append(status_names[idx])
            selected_data.append(data[idx])

        y = numpy.row_stack(tuple(selected_data))
        x = dates

        # Plotting
        fig, ax = plt.subplots()
        fig.set_size_inches(w=20.0, h=10)
        fig.suptitle("Cumulative Flow Diagram of {:s}".format(getattr(project, 'name')))
        plt.xlabel('Week', fontsize=18)
        plt.ylabel('Number of USs', fontsize=16)
        polys = ax.stackplot(x, y)

        # X-axis, plot per week.
        mondays = WeekdayLocator(MONDAY)
        weeks = WeekdayLocator(byweekday=MONDAY, interval=1)
        weeksFmt = DateFormatter("%W")
        ax.xaxis.set_major_locator(weeks)
        ax.xaxis.set_major_formatter(weeksFmt)
        ax.xaxis.set_minor_locator(mondays)
        ax.autoscale_view()
        fig.autofmt_xdate()

        # Generation date string
        date_now = time.strftime("%Y-%m-%d %H:%M:%S")
        date_str = "Generated at {:s}".format(date_now)
        fig.text(0.125, 0.1, date_str)

        # Legend
        ## Stack plot legend
        legendProxies = []
        for poly in polys:
            legendProxies.append(plt.Rectangle((0, 0), 1, 1, fc=poly.get_facecolor()[0]))
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

        ax.legend(reversed(legendProxies), reversed(selected_snames), title="Color chart", loc='center left',
                  bbox_to_anchor=(1, 0.5))

        # Generation date string
        date_now = time.strftime("%Y-%m-%d %H:%M:%S")
        date_str = "Generated at {:s}".format(date_now)
        fig.text(0.015, 0.015, date_str)

        figure = io.BytesIO()
        plt.savefig(figure, format="png")
        content_file = ImageFile(figure)
        random_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        project.cfd_image.save(random_name + '.png', content_file)
        project.save(update_fields=["cfd_image"])

        plt.close(fig)
        plt.gcf().clear()
        print('Generated cumulative png of project_' + str(getattr(project, 'id')))
    except ObjectDoesNotExist:
        return None


# функция генерации диаграммы скорости проекта
def velocity_gen(project):
    try:
        velocity_data = models.VelocityChart.objects.get(project=project, created_date=date.today())

        n_groups = len(getattr(velocity_data, 'project_sprints_velocities'))
        if n_groups != 0:
            total = []
            completed = []
            sprints_names = []
            for sprint in getattr(velocity_data, 'project_sprints_velocities'):
                total.append(sprint['total_points'])
                completed.append(sprint['closed_points'])
                sprints_names.append(sprint['name'])
            total = tuple(total)
            completed = tuple(completed)

            fig, ax = plt.subplots()

            # увеличиваем разрешение графика
            fig.set_size_inches(21.5, 10.5)

            index = numpy.arange(n_groups)
            bar_width = 0.35

            opacity = 0.4
            error_config = {'ecolor': '0.3'}

            rects1 = plt.bar(index, total, bar_width,
                             alpha=opacity,
                             color='gray',
                             error_kw=error_config,
                             label='Commitment')

            rects2 = plt.bar(index + bar_width, completed, bar_width,
                             alpha=opacity,
                             color='green',
                             error_kw=error_config,
                             label='Completed')

            plt.ylabel('Story Points')
            plt.title('Sprints of ' + getattr(project, 'name'))
            plt.xticks(index + bar_width / 2, tuple(sprints_names))
            plt.legend()

            plt.tight_layout()

            # Generation date string
            date_now = time.strftime("%Y-%m-%d %H:%M:%S")
            date_str = "Generated at {:s}".format(date_now)
            fig.text(0.015, 0.975, date_str)

            figure = io.BytesIO()
            plt.savefig(figure, format="png")
            content_file = ImageFile(figure)
            random_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
            project.velocity_image.save(random_name + '.png', content_file)
            project.save(update_fields=["velocity_image"])

            plt.close(fig)
            plt.gcf().clear()
            print('Generated velocity png of project_' + str(getattr(project, 'id')))
    except ObjectDoesNotExist:
        return None


DOT_HEADER_FMT = """digraph {{
  labelloc="t";
  //labelfontsize="40"
  label="{:s}";
  //size="7.5,10"
  ratio="compress"
  //orientation=landscape
"""


# функция генерации графика взаимозависимостей между требованиями заказчика проекта
def us_dependencies_gen(project):
    status_ids = None

    proj_attrs = UserStoryCustomAttribute.objects.filter(project=project)
    uss = UserStory.objects.filter(project=project)
    uss_statuses_queryset = UserStoryStatus.objects.filter(project=project)
    status_ids, _ = uss_statuses_queryset.values_list('id', flat=True)[
                    ::-1], uss_statuses_queryset.values_list('name', flat=True)[::-1]
    selected_sids = None
    selected_sids = status_ids

    for sid in selected_sids:
        try:
            idx = status_ids.index(sid)
        except ValueError:
            print("Selected US status ID {:d} not found for project {:s}!".format(sid, project.name))
            return 1

    selected_uss = []
    for us in uss:
        if getattr(us, 'status_id') in selected_sids:
            selected_uss.append(us)

    titles = []
    edges = []
    header = DOT_HEADER_FMT.format("US Dependency Graph")

    depson_attr_id = None
    for attr in proj_attrs:
        if getattr(attr, 'name') == 'Depends On':
            depson_attr_id = getattr(attr, 'id')
    if not depson_attr_id:
        print(
            "No custom User Story attribute named '{:s}' found!. Go to Settings>Attributes>Custom Fields and create one.".format(
                'Depends On'), file=sys.stderr)

    for us in selected_uss:
        if getattr(us, 'is_closed'):
            color = "green"
        else:
            color = "black"
        subject = re.sub("\"", '', us.subject)

        points = ""

        tags = ""

        attrs = getattr(UserStoryCustomAttributesValues.objects.get(user_story=us), 'attributes_values')
        if str(depson_attr_id) in attrs:
            deps = attrs[str(depson_attr_id)].split(',')
            for dep in deps:
                dep = dep.strip(' \t\n\r').lstrip('#')
                if dep:
                    edges.append('  "{:s}" -> "{:d}"'.format(dep, us.ref))

        titles.append(
            "  \"{:d}\" [label=\"#{:d} {:s}{:s}{:s}\", color=\"{:s}\"];".format(us.ref, us.ref, subject, tags, points,
                                                                                color))

    footer = '}'
    titles.sort()
    edges.sort()
    file_path = os.path.abspath(os.path.dirname(__file__)) + "/us_dependencies_dot_files/project_" + str(
        getattr(project, 'id')) + ".dot"
    try:
        with open(file_path, 'w') as fh:
            fh.write(header)
            fh.write("\n  // Edges\n")
            for edge in edges:
                fh.write("{:s}\n".format(edge))
            fh.write("\n  // Titles\n")
            for title in titles:
                fh.write("{:s}\n".format(title))
            fh.write(footer)
            print("Dependency graph data of project_{:d} written to: {:s}\n".format(getattr(project, 'id'), file_path))
    except IOError as err:
        print("Could not write file {:s}: {:s}".format(file_path, str(err)), file=sys.stderr)
        return 1


# генерация графика взаимозависимостей и форматирование в нем узлов между требованиями заказчика
def draw_us_dependencies(project):
    dot_path = os.path.abspath(os.path.dirname(__file__)) + '/us_dependencies_dot_files/project_' + str(
        getattr(project, 'id')) + '.dot'
    image_path = os.path.abspath(os.path.dirname(__file__)) + '/us_dependencies_images/project_' + str(
        getattr(project, 'id')) + '.png'
    os.system('dot -T png -o ' + image_path + ' ' + dot_path)
    os.system('unflatten -l1 -c5 ' + dot_path + ' | dot -T png -o ' + image_path)

    file = open(image_path, 'rb')
    random_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    project.us_dependencies_image.save(random_name + '.png', File(file))
    project.save(update_fields=["us_dependencies_image"])

    print('Generated us_dependencies png of project_' + str(getattr(project, 'id')))


###########################################################################
# Burndown, Burnup graphs forecast
###########################################################################


def get_project_burndown_release_and_sprints_forecast(project):
    # спринты с очками
    array_data = []
    # индекс для numpy манипуляций
    i = 1
    # coint
    coint = 0
    # даты спринтов проекта
    dates = []
    # данные статистики предыдущего спринта
    previous_sprint_without_none = None
    # данные статистики спринтов проекта
    project_milestones_stats = get_stats_for_project(project)['milestones']
    # если у первого спринта данного проекта очки по нулям, то переходим к следующему проекту
    if project_milestones_stats[0]['evolution'] == 0:
        return
    for sprint in project_milestones_stats:
        if sprint['id']:
            get_sprint_burndown_forecast(sprint['id'])
        if sprint['name'] == 'Future sprint' or sprint['name'] == 'Project End':
            coint += 1
        else:
            dates.append(sprint['name'])
            # если вместо очков стоит None, берём данные предыдущего спринта
            if sprint['evolution'] is None:
                array_data.append([i, previous_sprint_without_none['evolution']])
            else:
                array_data.append([i, sprint['evolution']])
                # запоминаем спринт
                previous_sprint_without_none = sprint
            # увеличиваем индекс для numpy манипуляций
            i += 1
    field_name = 'burndown_forecast_image'
    # генерим график
    forecast_graph_generating(project, field_name, array_data, dates, coint)
    print('Generated ' + field_name + ' of project_' + str(getattr(project, 'id')))


def get_sprint_burndown_forecast(milestone_id):
    milestone = Milestone.objects.get(pk=milestone_id)
    total_points = milestone.total_points

    # очки спринта
    array_data = []
    # дни спринта
    days = []
    # индекс для numpy манипуляций
    i = 1
    # coint
    coint = 0
    # для запоминания количества open_points предыдущего дня
    previous_open_points = 0

    current_date = milestone.estimated_start
    sumTotalPoints = sum(total_points.values())
    # для запоминания самого меньшего количества очков дней спринта
    min_sprint_open_points = sumTotalPoints - milestone.total_closed_points_by_date(milestone.estimated_finish)
    while current_date <= milestone.estimated_finish:
        open_points = sumTotalPoints - milestone.total_closed_points_by_date(current_date)
        if open_points == min_sprint_open_points and open_points == previous_open_points:
            coint += 1
        else:
            array_data.append([i, open_points])
            days.append(current_date.strftime("%B %d, %Y"))
            i += 1
        current_date = current_date + timedelta(days=1)
        previous_open_points = open_points

    field_name = 'burndown_forecast_image'
    # генерим график
    forecast_graph_generating(milestone, field_name, array_data, days, coint)
    print('Generated ' + field_name + ' of sprint_' + str(milestone_id) + ' of project_' + str(getattr(milestone, 'project_id')))

def get_release_burnup_forecast(project):
    try:
        burnup_data = models.BurnupChart.objects.get(project=project, created_date=date.today())
        sprints_days = [d['sprint_date'] for d in getattr(burnup_data, 'data') if 'sprint_date' in d]
        completed_points = [d['completed_points'] for d in getattr(burnup_data, 'data') if 'completed_points' in d]
        planned_sprints_count = getattr(project, 'total_milestones')
        # спринты с очками
        array_data = []
        # индекс для numpy манипуляций
        i = 1
        # coint
        coint = planned_sprints_count - len(completed_points)
        for elem in completed_points:
            array_data.append([i, elem])
            # увеличиваем индекс для numpy манипуляций
            i += 1
        field_name = 'burnup_forecast_image'
        # генерим график
        forecast_graph_generating(project, field_name, array_data, sprints_days, coint)
        print('Generated ' + field_name + ' of project_' + str(getattr(project, 'id')))
    except ObjectDoesNotExist:
        return None


# экстраполяция и построение графика
def forecast_graph_generating(object, field_name, array_data, dates, coint):
    fig, ax = plt.subplots()
    # подписываем график
    fig.suptitle(field_name + ' of ' + getattr(object, 'name'), fontsize=20)
    # добавляем сетку на график
    plt.grid()

    if len(array_data) > 3:
        new_points_coint = coint
        # преобразуем лист в numpy массив
        data = numpy.array(array_data)
        fit = numpy.polyfit(data[:, 0], data[:, 1], 1)
        line = numpy.poly1d(fit)
        new_points = numpy.arange(new_points_coint) + len(data) + 1
        new_y = line(new_points)
        new_y[new_y < 0] = 0
        noise = numpy.random.normal(new_y, scale=(numpy.average(data) / 10), size=len(new_y))
        noise[noise < 0] = 0
        new_ywn = noise
        data_line = numpy.stack((new_points, new_y), axis=-1)
        data_line = numpy.append(data, data_line, axis=0)
        data2 = numpy.stack((new_points, new_ywn), axis=-1)
        data3 = numpy.append(data[3:], data2, axis=0)
        data4 = data3[:, 1]
        data4[data4 < 0] = 0
        data_z = numpy.where(data4 == 0)[0]
        if data_z.any():
            data5 = (data4[:data_z[0] + 1])
        else:
            data5 = data4
        # строим график
        ax.plot(data[:, 0], data[:, 1], 'r')
        ax.plot(data3[:, 0], data3[:, 1], 'green')
        ax.plot(data_line[:, 0], data_line[:, 1], 'r--')
        axis_points_template = numpy.arange(min(data[:, 0]), max(data3[:, 0]) + 1, 1.0)
        plt.xticks(axis_points_template)
        dates.extend(['Future object'] * coint)
        # подписываем ось абсцисс датами
        ax.set_xticklabels(dates, minor=False, rotation=45)
        plt.ylabel('Story Points')
    else:
        plt.text(0.5, 0.5, "Количество предыдущих объектов < 4, экстраполяция невозможна", size=25, rotation=0,
                 ha="center", va="center",
                 bbox=dict(boxstyle="round",
                           ec=(1., 0.5, 0.5),
                           fc=(1., 0.8, 0.8),
                           )
                 )
    # увеличиваем разрешение графика
    fig.set_size_inches(17.5, 12.5)

    # Generation date string
    date_now = time.strftime("%Y-%m-%d %H:%M:%S")
    date_str = "Generated at {:s}".format(date_now)
    fig.text(0.015, 0.015, date_str)

    figure = io.BytesIO()
    plt.savefig(figure, format="png")
    content_file = ImageFile(figure)
    random_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    getattr(object, field_name).save(random_name + '.png', content_file)
    object.save(update_fields=[field_name])

    plt.close(fig)
    plt.gcf().clear()


# функция генерации всех графиков по текущим данным определенного проекта
def generate_charts(project):
    burnup_gen(project)
    cumulative_flow_gen(project)
    velocity_gen(project)
    us_dependencies_gen(project)
    draw_us_dependencies(project)


# обновление данных и генерация графиков для всех проектов в платформе
def update_stats_charts():
    # Если нет директорий для us_dependenices, создаём
    if not os.path.exists(os.path.abspath(os.path.dirname(__file__)) + '/us_dependencies_dot_files'):
        os.makedirs(os.path.abspath(os.path.dirname(__file__)) + '/us_dependencies_dot_files')
    if not os.path.exists(os.path.abspath(os.path.dirname(__file__)) + '/us_dependencies_images'):
        os.makedirs(os.path.abspath(os.path.dirname(__file__)) + '/us_dependencies_images')

    # todo В дальнейшем (когда количество проектов значительно увеличится) необходимо распараллелить данный процесс
    # todo Либо перевести генерацию статистики в live-режим, а построение графиков выполнять на клиенте (исключение – CFD), но это может увеличить время загрузки Backlog страницы проекта
    for project in Project.objects.all():
        generate_stats(project)
        generate_charts(project)
        get_project_burndown_release_and_sprints_forecast(project)
        get_release_burnup_forecast(project)


###########################################################################
# Agile Stats Data Export
###########################################################################
def export_project_stats_by_date_xls(request, project_id):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment;'

    project_name = getattr(Project.objects.get(pk=project_id), 'name')

    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    wb = xlwt.Workbook(encoding='utf-8')
    columns = ['id', 'created_date', 'project id', 'data', 'project name']

    ws = wb.add_sheet('Burnup')
    # Sheet header, first row
    row_num = 0
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num])
    burnup_rows = models.BurnupChart.objects.filter(project_id=project_id).values_list('id', 'created_date', 'project_id', 'data')
    for row in burnup_rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]))
        ws.write(row_num, len(row), project_name)

    ws = wb.add_sheet('CFD')
    # Sheet header, first row
    row_num = 0
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num])
    cfd_rows = models.CumulativeFlowDiagram.objects.filter(project_id=project_id).values_list('id', 'created_date', 'project_id', 'data')
    for row in cfd_rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]))
        ws.write(row_num, len(row), project_name)

    ws = wb.add_sheet('Velocity')
    # Sheet header, first row
    row_num = 0
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num])
    velocity_rows = models.VelocityChart.objects.filter(project_id=project_id).values_list('id', 'created_date', 'project_id', 'project_sprints_velocities')
    for row in velocity_rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]))
        ws.write(row_num, len(row), project_name)

    wb.save(response)
    return response


# геймификация
def update_users_projects_activity():
    # получаем всех юзеров
    all_users = User.objects.all()
    # пробегаемся по юзерам
    for user in all_users:
        # конечный json, содержащий данные по активности в каждом проекте
        user_activity = {}
        # получаем список проектов, в которых юзер активничал за последние сутки
        was_active_in_project_ids = HistoryEntry.objects.filter(user__pk=getattr(user, 'id'), created_at__date=datetime.now().date()).order_by().values_list('project_id', flat=True).distinct()
        # получаем список проектов, в которых участвует юзер
        user_in_projects = user.cached_memberships
        # пробегаемся по списку user_in_projects и сверяем со списком was_active_in_project_ids
        for project in user_in_projects:
            # достаём текущий проект по id из БД
            project_full_obj = Project.objects.get(pk=getattr(project, 'project_id'))
            # дефолтное количество очков проекта, прибавляемое за активность участников
            default_gamification_points = getattr(project_full_obj, 'default_gamification_points')
            # массив активности в проекте
            project_activity = {}
            # если активность в проекте за сегодня была
            if getattr(project, 'project_id') in was_active_in_project_ids:
                # если в бд у юзера отсутствуют данные по активности в проектах
                if not getattr(user, 'projects_activity'):
                    project_activity['points'] = default_gamification_points
                # если в бд у юзера присутствуют данные по активности в проектах
                else:
                    # инкрементируем предыдущее количество очков
                    project_activity['points'] = getattr(user, 'projects_activity')[str(getattr(project, 'project_id'))]['points'] + default_gamification_points
                project_activity['isDowngrade'] = False
            # если активности в проекте за сегодня не было
            else:
                # если в бд у юзера отсутствуют данные по активности в проектах
                if not getattr(user, 'projects_activity'):
                    project_activity['points'] = 0
                    project_activity['isDowngrade'] = False
                # если в бд у юзера присутствуют данные по активности в проектах
                else:
                    # получаем все незакрытые таски юзера в текущем проекте
                    user_project_open_tasks = Task.objects.filter(assigned_to_id=getattr(user, 'id'), project=project_full_obj, finished_date=None)
                    # если предыдущее количество очков юзера было > 0 и при этом есть незакрытые в данном проекте таски, то сбрасываем очки
                    if getattr(user, 'projects_activity')[str(getattr(project, 'project_id'))]['points'] > 0 and user_project_open_tasks:
                        project_activity['points'] = 0
                        # юзер потерял все свои предыдущие очки
                        project_activity['isDowngrade'] = True
                    else:
                        project_activity['points'] = getattr(user, 'projects_activity')[str(getattr(project, 'project_id'))]['points']
                        project_activity['isDowngrade'] = False
            user_activity[getattr(project, 'project_id')] = project_activity
        # сохраняем в бд новые данные об активности юзера
        user.projects_activity = user_activity
        user.save()
