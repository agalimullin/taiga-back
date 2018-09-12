# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Taiga Agile LLC <taiga@taiga.io>
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


def get_burnup_image_url(project):
    if project.burnup_image and project.burnup_image.url:
        return project.burnup_image.url
    return None


def get_cfd_image_url(project):
    if project.cfd_image and project.cfd_image.url:
        return project.cfd_image.url
    return None


def get_velocity_image_url(project):
    if project.velocity_image and project.velocity_image.url:
        return project.velocity_image.url
    return None


def get_us_dependencies_image_url(project):
    if project.us_dependencies_image and project.us_dependencies_image.url:
        return project.us_dependencies_image.url
    return None


def get_burndown_forecast_image_url(project):
    if project.burndown_forecast_image and project.burndown_forecast_image.url:
        return project.burndown_forecast_image.url
    return None


def get_burnup_forecast_image_url(project):
    if project.burnup_forecast_image and project.burnup_forecast_image.url:
        return project.burnup_forecast_image.url
    return None
