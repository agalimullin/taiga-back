# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from taiga.base.db.models.fields import JSONField
from django.utils import timezone
import datetime


class BurnupChart(models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="burnup_chart_stats", verbose_name=_("project"))
    total_points = JSONField(null=False, blank=False, verbose_name=_("total points"))
    completed_points = JSONField(null=False, blank=False, verbose_name=_("completed points"))
    created_date = models.DateField(null=False, blank=False,
                                    verbose_name=_("created date"),
                                    default=datetime.date.today)

    class Meta:
        verbose_name = "burnup chart"
        verbose_name_plural = "burnup charts"
        ordering = ["created_date", "project_id"]


class CumulativeFlowDiagram(models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="cumulative_flow_diagram_stats", verbose_name=_("project"))
    data = JSONField(null=False, blank=False, verbose_name=_("data"))
    # dates = JSONField(null=False, blank=False, verbose_name=_("dates"))
    # annotations = JSONField(null=False, blank=False, verbose_name=_("annotations"))
    # all_archieved = JSONField(null=False, blank=False, verbose_name=_("all archieved"))
    # all_done = JSONField(null=False, blank=False, verbose_name=_("all done"))
    # all_ready_for_test = JSONField(null=False, blank=False, verbose_name=_("all ready for test"))
    # all_in_progress = JSONField(null=False, blank=False, verbose_name=_("all in progress"))
    # all_ready = JSONField(null=False, blank=False, verbose_name=_("all ready"))
    # all_new = JSONField(null=False, blank=False, verbose_name=_("all new"))
    created_date = models.DateField(null=False, blank=False,
                                    verbose_name=_("created date"),
                                    default=datetime.date.today)

    class Meta:
        verbose_name = "cumulative flow diagram"
        verbose_name_plural = "cumulative flow diagrams"
        ordering = ["created_date", "project_id"]


class VelocityChart(models.Model):
    project = models.ForeignKey("projects.Project", null=False, blank=False,
                                related_name="velocity_chart_stats", verbose_name=_("project"))
    project_sprints_velocities = JSONField(null=False, blank=False, verbose_name=_("project sprints velocities"))
    created_date = models.DateField(null=False, blank=False,
                                    verbose_name=_("created date"),
                                    default=datetime.date.today)

    class Meta:
        verbose_name = "velocity chart"
        verbose_name_plural = "velocity charts"
        ordering = ["created_date", "project_id"]
