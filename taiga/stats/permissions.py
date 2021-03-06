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


from taiga.base.api import permissions


class SystemStatsPermission(permissions.TaigaResourcePermission):
    global_perms = permissions.AllowAny()


class DiscoverStatsPermission(permissions.TaigaResourcePermission):
    global_perms = permissions.AllowAny()


class StatsExportPermission(permissions.TaigaResourcePermission):
    project_admin_perms = permissions.IsProjectAdmin
