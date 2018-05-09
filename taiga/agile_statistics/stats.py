from pprint import pprint
import argparse
import configparser
import datetime as dt
import os
import re
import sys
import time
import numpy
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mplotdates
from matplotlib.dates import MONDAY
from matplotlib.dates import MonthLocator, WeekdayLocator, DateFormatter
import taiga.agile_statistics.taiga_external_api as taiga
from settings import MEDIA_ROOT

################# Constants #####################
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))  # разобраться
NOW = dt.datetime.now()
CURRENT_DATE_FULL = str(NOW.day) + '_' + str(NOW.month) + '_' + str(NOW.year)
YESTERDAY = NOW - dt.timedelta(days=1)
YESTERDAY_CFD_PATH = "{:s}/{:s}".format(CURRENT_DIR,  'cfd_dat/' + str(YESTERDAY.day) + '_' + str(YESTERDAY.month) + '_' + str(YESTERDAY.year))
CFD_DATA_FILE_FMT = 'cfd_dat/{:s}/cfd_{:s}.dat'
CFD_OUT_PNG_FMT = MEDIA_ROOT + '/agile_stats_snapshots/cfd/{:s}/cfd_{:s}.png'
NO_ANNOTATION = 'NONE'
TAG_MATCH_ALL = '*'
CUST_ATTRIB_DEPENDSON_NAME = 'Depends On'

CONF_FILE_PATH = CURRENT_DIR + '/taiga-stats.conf'
CONF_FILE_NAME_FMT = CURRENT_DIR + '/taiga.conf.template'

DEPS_DOT_FILE_FMT = 'deps_dat/dependencies_{:s}'

DOT_HEADER_FMT = """digraph {:s} {{
  labelloc="t";
  //labelfontsize="40"
  label="{:s}";
  //size="7.5,10"
  ratio="compress"
  //orientation=landscape
"""


################# Helper functions #####################

def get_tag_str(tag):
    return "" if tag == TAG_MATCH_ALL else tag


def get_stories_with_tag(project, tag):
    uss = project.list_user_stories()
    ret_uss = None
    if tag == TAG_MATCH_ALL:
        ret_uss = uss
    else:
        ret_uss = []
        for us in uss:
            if us.tags and tag in us.tags:
                ret_uss.append(us)

    if ret_uss is None or len(ret_uss) == 0:
        print("Warning: no userstories matching '{:s}' was found.".format(tag), file=sys.stderr)
        # sys.exit(1)
    return ret_uss


def get_us_stauts_id_from_name(project, name):
    statuses = project.list_user_story_statuses()
    for status in statuses:
        if status.name == name:
            return status.id
    return None


def get_us_status_name_from_id(project, status_id):
    statuses = project.list_user_story_statuses()
    for status in statuses:
        if status.id == status_id:
            return status.name
    return None


def remove_closed_stories(project, uss):
    ret_uss = []
    for us in uss:
        if not us.is_closed:
            ret_uss.append(us)
    return ret_uss


def get_statuses_sorted_by_order(project):
    statuses = project.list_user_story_statuses()
    return sorted(statuses, key=lambda status: status.order)


def get_statuses_sorted_by_id(project):
    statuses = project.list_user_story_statuses()
    return sorted(statuses, key=lambda status: status.id)


def get_status_id_sorted(project):
    return [status.id for status in get_statuses_sorted_by_order(project)]


def get_status_and_names_sorted(project):
    status_ids = get_status_id_sorted(project)[::-1]
    status_names = []
    for status_id in status_ids:
        status_names.append(get_us_status_name_from_id(project, status_id))

    return status_ids, status_names


def get_dot_header(name, title):
    return DOT_HEADER_FMT.format(name, title)


def get_dot_footer():
    return "}"


def read_daily_cfd(path, tag, project_id):
    data_file = CFD_DATA_FILE_FMT.format(CURRENT_DATE_FULL, 'project_' + str(project_id))
    data_path = "{:s}/{:s}".format(CURRENT_DIR, data_file)
    data = []
    try:
        with open(data_path, 'r') as fdata:
            row = 0
            for line in fdata:
                line = line.rstrip()
                parts = line.split('\t')
                if row == 0:
                    data = [[] for _ in range(len(parts) + 1)]
                else:
                    for col in range(len(parts)):
                        value = parts[col]
                        if col == 0:  # First col is dates
                            value = dt.datetime.strptime(value, "%Y-%m-%d")
                        elif col == 1:  # Second col is annotations
                            pass
                        else:
                            value = int(value)
                        data[col].append(value)

                row += 1
    except IOError as e:
        print("Could not read {:s}, error: {:s}".format(data_path, str(e)), file=sys.stderr)
        sys.exit(2)
    return data


################# Commands #####################

def cmd_list_projects(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])

    print("All projects which you have access to:")
    print("id\tname")
    print("--\t----")
    for proj in api.projects.list():
        print("{:-3d}\t{:s}".format(proj.id, proj.name))

    return 0


def cmd_list_us_statuses(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project = api.projects.get(args['project_id'])

    print("Statuses for project \"{:s}\"".format(project.name))
    print("order\tid\tname")
    print("--\t----")
    statuses = get_statuses_sorted_by_order(project)
    for status in statuses:
        print("{:d}\t{:-4d}\t{:s}".format(status.order, status.id, status.name))

    return 0


def cmd_print_us_in_dep_format(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project = api.projects.get(args['project_id'])
    tag = args['tag']
    status_ids = None

    status_ids, _ = get_status_and_names_sorted(project)
    selected_sids = None
    if 'status_ids' in args and args['status_ids']:
        selected_sids = [int(sid) for sid in args['status_ids'].split(',')]
        selected_sids.reverse()
    else:
        selected_sids = status_ids

    for sid in selected_sids:
        try:
            idx = status_ids.index(sid)
        except ValueError:
            print("Selected US status ID {:d} not found for project {:s}!".format(sid, project.name))
            return 1

    uss = get_stories_with_tag(project, tag)

    selected_uss = []
    for us in uss:
        if us.status in selected_sids:
            selected_uss.append(us)

    for us in selected_uss:
        if us.is_closed:
            color = "green"
        else:
            color = "black"
        subject = re.sub("\"", '', us.subject)
        print("  \"{:d}\" [label=\"#{:d} {:s}\", color=\"{:s}\"];".format(us.ref, us.ref, subject, color))

    return 0


def cmd_us_in_dep_format_dot(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project = api.projects.get(args['project_id'])
    tag = args['tag']
    output_path = args['output_path']
    status_ids = None
    print_tags = args['print_tags']
    print_points = args['print_points']

    status_ids, _ = get_status_and_names_sorted(project)
    selected_sids = None
    if 'status_ids' in args and args['status_ids']:
        selected_sids = [int(sid) for sid in args['status_ids'].split(',')]
        selected_sids.reverse()
    else:
        selected_sids = status_ids

    for sid in selected_sids:
        try:
            idx = status_ids.index(sid)
        except ValueError:
            print("Selected US status ID {:d} not found for project {:s}!".format(sid, project.name))
            return 1

    uss = get_stories_with_tag(project, tag)

    selected_uss = []
    for us in uss:
        if us.status in selected_sids:
            selected_uss.append(us)

    titles = []
    edges = []
    header = get_dot_header(get_tag_str(tag), "{:s} US Dependency Graph".format(get_tag_str(tag)))

    depson_attr_id = None
    proj_attrs = project.list_user_story_attributes()
    for attr in proj_attrs:
        if attr.name == CUST_ATTRIB_DEPENDSON_NAME:
            depson_attr_id = attr.id
    if not depson_attr_id:
        print(
            "No custom User Story attribute named '{:s}' found!. Go to Settings>Attributes>Custom Fields and create one.".format(
                CUST_ATTRIB_DEPENDSON_NAME), file=sys.stderr)
        return 1

    for us in selected_uss:
        if us.is_closed:
            color = "green"
        else:
            color = "black"
        subject = re.sub("\"", '', us.subject)

        points = ""
        if print_points and us.total_points:
            points += '\n{:s} points'.format(str(us.total_points))
            points = points.replace("\n", "\\n")  # Don't interpret \n.

        tags = ""
        if print_tags and us.tags:
            tags += '\n['
            for ustag in us.tags:
                tags += "{:s}, ".format(ustag)
            tags = tags[:-2]  # Remove last ", "
            tags += ']'
            tags = tags.replace("\n", "\\n")  # Don't interpret \n.

        attrs = us.get_attributes()
        if str(depson_attr_id) in attrs['attributes_values']:
            deps = attrs['attributes_values'][str(depson_attr_id)].split(',')
            for dep in deps:
                dep = dep.strip(' \t\n\r').lstrip('#')
                if dep:
                    edges.append('  "{:s}" -> "{:d}"'.format(dep, us.ref))

        titles.append(
            "  \"{:d}\" [label=\"#{:d} {:s}{:s}{:s}\", color=\"{:s}\"];".format(us.ref, us.ref, subject, tags, points,
                                                                                color))

    footer = get_dot_footer()
    titles.sort()
    edges.sort()

    file_name_base = DEPS_DOT_FILE_FMT.format(str(args['project_id']))
    file_name = file_name_base + ".dot"
    file_path = "{:s}/{:s}".format(CURRENT_DIR, file_name)
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
            print("Dependency graph written to: {:s}\n".format(file_path))
            print("Generate a png with e.g.")
            print("$ dot -T png -o {:s}/{:s}.png {:s}".format(output_path, file_name_base, file_path))
            print("$ unflatten -l1 -c5 {:s}/{:s} | dot -T png -o {:s}/{:s}.png".format(output_path, file_name,
                                                                                       output_path, file_name_base))
    except IOError as err:
        print("Could not write file {:s}: {:s}".format(file_path, str(err)), file=sys.stderr)
        return 1

    return 0


def deps_gen(dataPath, snapshotPath):
    os.system('unflatten -l1 -c5 ' + dataPath + ' | dot -T png -o ' + snapshotPath)


def cmd_points_sum(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project = api.projects.get(args['project_id'])
    tag = args['tag']
    status_ids = None

    status_ids, _ = get_status_and_names_sorted(project)
    selected_sids = None
    if 'status_ids' in args and args['status_ids']:
        selected_sids = [int(sid) for sid in args['status_ids'].split(',')]
        selected_sids.reverse()
    else:
        selected_sids = status_ids

    for sid in selected_sids:
        try:
            idx = status_ids.index(sid)
        except ValueError:
            print("Selected US status ID {:d} not found for project {:s}!".format(sid, project.name))
            return 1

    uss = get_stories_with_tag(project, tag)

    selected_uss = []
    for us in uss:
        if us.status in selected_sids:
            selected_uss.append(us)

    points = {}  # statusID -> pointsum
    for us in selected_uss:
        if us.status not in points:
            points[us.status] = 0
        if us.total_points:
            points[us.status] += float(us.total_points)

    for status_id, points_sum in points.items():
        status_name = get_us_status_name_from_id(project, status_id)
        print("{:20s}\t{:.1f}".format(status_name, points_sum))


def velocity_gen(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project = api.projects.get(args['project_id'])
    project_milestones = reversed(project.list_milestones())
    velocity = []  # sprints velocities

    if project_milestones:
        for milestone in project_milestones:
            milestone = vars(milestone)
            if milestone['closed_points']:
                closed_points = velocity.append(milestone['closed_points'])
            else:
                closed_points = velocity.append(0)

    N = len(velocity)

    tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
                 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                 (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                 (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229),
                 (238, 99, 99)]

    # Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
    for i in range(len(tableau20)):
        r, g, b = tableau20[i]
        tableau20[i] = (r / 255., g / 255., b / 255.)

    fig = plt.figure(figsize=(12, 14))
    ax = fig.add_subplot(111)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()


    ## necessary variables
    ind = numpy.arange(N)  # the x locations for the groups
    width = 0.9  # the width of the bars

    velocity_mean = [numpy.mean(velocity) for i in range(1, N)]

    rects2 = ax.bar(ind + width, velocity, width, color=tableau20[20])

    # axes and labels
    plt.yticks(range(0, 45, 10), [str(x) for x in range(0, 45, 10)], fontsize=22)
    plt.xticks(fontsize=22)
    ax.set_xlim(width, len(ind) + width)
    ax.set_ylim(0, 45)
    ax.set_ylabel('Story Points', fontsize=22)
    ax.set_xlabel('Iterations', fontsize=22)
    # ax.set_title('Velocity for each Iteration')
    xTickMarks = ['Iter- ' + str(i) for i in range(1, 10)]
    ax.set_xticks(ind + width)
    xtickNames = ax.set_xticklabels(xTickMarks)

    mean_line = ax.plot(range(1, N), velocity_mean, label='Mean',
                        linestyle='--', linewidth=3, color=tableau20[10])

    plt.setp(xtickNames, rotation=45, fontsize=22)
    legend = ax.legend(loc='upper right')

    # сохраняем график в файл
    if not os.path.isdir(MEDIA_ROOT + '/agile_stats_snapshots/velocity/' + CURRENT_DATE_FULL):
        os.makedirs(MEDIA_ROOT + '/agile_stats_snapshots/velocity/' + CURRENT_DATE_FULL)
    out_file = MEDIA_ROOT + '/agile_stats_snapshots/velocity/' + CURRENT_DATE_FULL + '/velocity_project_%s.png' % str(args['project_id'])
    plt.savefig(out_file)
    print("velocity_{:s} generated at: {:s}".format('project_' + str(args['project_id']), out_file))


def cmd_print_burnup_data(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project = api.projects.get(args['project_id'])
    project_name = args['project_name']
    total_project_points = vars(project)['total_story_points']  # total project points
    project_milestones = reversed(project.list_milestones())
    totals = []  # data in sprints

    #toDo комменты добавить
    if project_milestones:
        previous_closed = 0
        for milestone in project_milestones:
            milestone = vars(milestone)
            if milestone['closed_points']:
                closed_points = milestone['closed_points']
            else:
                closed_points = 0
            closed_points += previous_closed
            totals.append({
                'sprint_name': milestone['name'],
                'sprint_start': milestone['estimated_start'],
                'closed_points': closed_points
            })
            previous_closed += closed_points
    # sprint names
    x = []
    # sprint full needed points
    if not total_project_points:
        total_points = [0] * len(totals)
    else:
        total_points = [total_project_points] * len(totals)
    # sprint current points
    completed_points = []
    for total in totals:
        x.append(total['sprint_start'])
        # total_points.append(total['total_points'])
        completed_points.append(total['closed_points'])

    fig, ax = plt.subplots()

    fig.suptitle("Burnup chart of {:s}".format(str(project_name)))

    # добавляем на грабик линии с total_points, completed_points
    ax.plot(x, total_points, 'bs-')
    ax.plot(x, completed_points, 'rs-')

    # подписываем ось Y
    plt.ylabel('Points')
    # добавляем сетку на график
    plt.grid()
    # поворачиваем и устанавливаем подписи точек на оси X
    plt.xticks(rotation=45)

    # добавляем легенду
    plt.plot(x, total_points, '-b', label='Total points')
    plt.plot(x, completed_points, '-r', label='Completed points')
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # увеличиваем разрешение графика
    fig.set_size_inches(21.5, 10.5)

    # подписываем каждую точку графика
    for X, Y in zip(x, completed_points):
        # если есть координата Y (completed sprint points)
        if Y:
            ax.annotate('{}'.format(Y), xy=(X, Y), xytext=(-5, 5), ha='right',
                        textcoords='offset points')
    # сохраняем график в файл
    if not os.path.isdir(MEDIA_ROOT + '/agile_stats_snapshots/burnup/' + CURRENT_DATE_FULL):
        os.makedirs(MEDIA_ROOT + '/agile_stats_snapshots/burnup/' + CURRENT_DATE_FULL)
    out_file = MEDIA_ROOT + '/agile_stats_snapshots/burnup/' + CURRENT_DATE_FULL + '/burnup_project_%s.png' % str(args['project_id'])
    plt.savefig(out_file)
    print("burnup_{:s} generated at: {:s}".format('project_' + str(args['project_id']), out_file))


def cmd_store_daily_stats(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project_id = args['project_id']
    project = api.projects.get(args['project_id'])
    tag = args['tag']
    output_path = args['output_path']

    status_ids, _ = get_status_and_names_sorted(project)
    uss = get_stories_with_tag(project, tag)
    us_by_status = {status_id: [] for status_id in status_ids}
    for us in uss:
        us_by_status[us.status].append(us)

    if not os.path.isdir(CURRENT_DIR + '/cfd_dat/' + CURRENT_DATE_FULL):
        os.makedirs(CURRENT_DIR + '/cfd_dat/' + CURRENT_DATE_FULL)
    data_file = CFD_DATA_FILE_FMT.format(CURRENT_DATE_FULL, 'project_' + str(project_id))
    data_path = "{:s}/{:s}".format(CURRENT_DIR, data_file)
    if not os.path.isfile(data_path):
        with open(data_path, 'w') as fdata:
            output = ''
            if os.path.exists(YESTERDAY_CFD_PATH):
                with open(YESTERDAY_CFD_PATH + '/cfd_project_' + str(project_id) + '.dat', 'r') as f:
                    output = f.read()
                fdata.write(output)
            else:
                fdata.write("#date")
                fdata.write("\tannotation")
                fdata.write("\tannotation_layer")
                for status_id in status_ids:
                    fdata.write("\t{:s}".format(get_us_status_name_from_id(project, status_id)))
                fdata.write("\n")

    with open(data_path, 'a') as fdata:
        fdata.write("{:s}".format(dt.datetime.utcnow().strftime("%Y-%m-%d")))
        fdata.write("\t{:s}".format(NO_ANNOTATION))
        fdata.write("\t{:d}".format(0))
        for status_id in status_ids:
            no_uss = len(us_by_status[status_id])
            fdata.write("\t{:d}".format(no_uss))
        fdata.write("\n")

    tag_str = " for {:s}".format(tag) if tag != TAG_MATCH_ALL else ""
    print("Daily stats of {:s} stored at: {:s}".format('project_' + str(project_id), data_path))

    return 0


def cmd_gen_cfd(args):
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])
    project_id = args['project_id']
    project_name = args['project_name']
    project = api.projects.get(args['project_id'])
    tag = args['tag']
    output_path = args['output_path']
    target_date = None
    target_layer = None
    status_ids = None
    annotations_off = args['annotations_off']

    # Data
    data = read_daily_cfd(output_path, tag, project_id)
    dates = data[0]
    annotations = data[1]
    annotation_layer = data[2]
    data = data[3:]

    status_ids, status_names = get_status_and_names_sorted(project)
    selected_sids = None
    if 'status_ids' in args and args['status_ids']:
        # Ids are plotted in the reversed order
        selected_sids = [int(sid) for sid in args['status_ids'].split(',')]
        selected_sids.reverse()
    else:
        selected_sids = status_ids

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
    tag_str = " for {:s}".format(tag) if tag != TAG_MATCH_ALL else ""
    fig.suptitle("Cumulative Flow Diagram of {:s}".format(str(project_name)))
    plt.xlabel('Week', fontsize=18)
    plt.ylabel('Number of USs', fontsize=16)
    polys = ax.stackplot(x, y)

    # X-axis, plot per week.
    mondays = WeekdayLocator(MONDAY)
    # months = MonthLocator(range(1, 13), bymonthday=1, interval=1)
    # monthsFmt = DateFormatter("%b '%y")
    weeks = WeekdayLocator(byweekday=MONDAY, interval=1)
    # weeksFmt = DateFormatter("%W ('%y)")
    weeksFmt = DateFormatter("%W")
    ax.xaxis.set_major_locator(weeks)
    ax.xaxis.set_major_formatter(weeksFmt)
    ax.xaxis.set_minor_locator(mondays)
    ax.autoscale_view()
    # ax.grid(True)
    fig.autofmt_xdate()

    if not annotations_off:
        # Draw annotations of the data.
        bbox_props = dict(boxstyle="round4,pad=0.3", fc="white", ec="black", lw=2)
        for i, annotation in enumerate(annotations):
            if annotation != NO_ANNOTATION:
                y_coord = 0  # Calculate the Y coordnate by stacking up y values below.
                for j in range(annotation_layer[i] + 1):
                    y_coord += y[j][i]
                ax.text(x[i], (y_coord + 5), annotation, ha="center", va="center", rotation=30, size=10,
                        bbox=bbox_props)

    # Generation date string
    date_now = time.strftime("%Y-%m-%d %H:%M:%S")
    date_str = "Generated at {:s}".format(date_now)
    fig.text(0.125, 0.1, date_str)

    # Ideal pace line
    print_ideal = False
    if ('target_date' in args and args['target_date']) and ('target_layer' in args and args['target_layer']):
        print_ideal = True
        target_date = args['target_date']
        target_date_dt = dt.datetime.strptime(target_date, "%Y-%m-%d")
        if mplotdates.date2num(target_date_dt) < mplotdates.date2num(x[0]):
            print("Target date must be after the first data point stored!", file=sys.stderr)

        target_layer = int(args['target_layer'])
        if not (0 <= target_layer < len(y)):
            print("Ideal target layer not in range!", file=sys.stderr)
            return 1

        y_ideal_start = 0
        for i in range(target_layer - 1):
            y_ideal_start += y[i][0]
        y_ideal_end = 0
        for i in range(target_layer + 1):
            y_ideal_end += y[i][-1]

        ideal_line = plt.plot([x[0], target_date_dt], [y_ideal_start, y_ideal_end], color='k', linestyle='--',
                              linewidth=3, label="Ideal Pace")

        # Extend last known value of target layer if needed.
        if mplotdates.date2num(x[-1]) < mplotdates.date2num(target_date_dt):
            plt.hlines(y_ideal_end, x[-1], target_date_dt, colors='k', linestyles='--', linewidth=3)

    # Legend
    ## Stack plot legend
    legendProxies = []
    for poly in polys:
        legendProxies.append(plt.Rectangle((0, 0), 1, 1, fc=poly.get_facecolor()[0]))
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ## Ideal line legend
    if print_ideal:
        legendProxies.append(
            plt.Line2D((0, 1), (0, 0), color=ideal_line[0].get_color(), linestyle=ideal_line[0].get_linestyle(),
                       linewidth=ideal_line[0].get_linewidth()))
        selected_snames.append(ideal_line[0].get_label())

    ax.legend(reversed(legendProxies), reversed(selected_snames), title="Color chart", loc='center left',
              bbox_to_anchor=(1, 0.5))

    if not os.path.isdir(MEDIA_ROOT + '/agile_stats_snapshots/cfd/' + CURRENT_DATE_FULL):
        os.makedirs(MEDIA_ROOT + '/agile_stats_snapshots/cfd/' + CURRENT_DATE_FULL)
    out_file = CFD_OUT_PNG_FMT.format(CURRENT_DATE_FULL, 'project_' + str(project_id))
    # out_path = "{:s}/{:s}".format(output_path, out_file)
    plt.savefig(out_file)

    # print("CFD{:s} generated at: {:s}".format(tag_str, out_path))
    print("CFD{:s} generated at: {:s}".format(tag_str, out_file))
    return 0


def cmd_gen_config_template(args):
    output_path = args['output_path']

    config = configparser.ConfigParser()
    config['taiga'] = {
        'url': 'https://api.taiga.io/',
        'auth_token': '',
    }
    config['default_values'] = {
        'project_id': '',
        'tag': '',
        'output_path': '',
        'target_date': '',
        'target_layer': '',
        'status_ids': '',
    }

    fpath = "{:s}/{:s}".format(output_path, CONF_FILE_NAME_FMT)
    try:
        with open(fpath, 'w') as configfile:
            config.write(configfile)
    except IOError:
        print("Could not create {:s}".format(fpath), file=sys.stderr)
        return 1

    print("Template created. Rename and edit it:\n$ mv {:s} {:s}".format(fpath, CONF_FILE_PATH))
    return 0


################# Main configuration #####################

# функция для считывания конфигурации API из файла
def read_config():
    url = None
    auth_token = None

    config = configparser.ConfigParser()
    config.read(os.path.expanduser(CONF_FILE_PATH))
    if 'api' in config:
        api = config['api']
        if 'url' in api:
            url = api['url']
        if 'auth_token' in api:
            auth_token = api['auth_token']

    return url, auth_token


COMMAND2FUNC = {
    'burnup': cmd_print_burnup_data,
    'velocity': velocity_gen,
    'cfd': cmd_gen_cfd,
    'config_template': cmd_gen_config_template,
    'deps_dot_nodes': cmd_print_us_in_dep_format,
    'deps_dot': cmd_us_in_dep_format_dot,
    'deps_gen': deps_gen,
    'list_projects': cmd_list_projects,
    'list_us_statuses': cmd_list_us_statuses,
    'store_daily': cmd_store_daily_stats,
    'points_sum': cmd_points_sum,
}


# def parse_args():
#     parser = argparse.ArgumentParser(
#         description="Taiga statistic tool. Default values for many options can be set config file; see the command 'config_template'.")
#
#     # General options
#     parser.add_argument('--url', help="URL to Taiga server.")
#     parser.add_argument('--auth-token',
#                         help="Authentication token. Instructions on how to get one is found at {:s}".format(
#                             'https://taigaio.github.io/taiga-doc/dist/api.html#_authentication'))
#
#     # Common options to commands
#     opt_tag = argparse.ArgumentParser(add_help=False)
#     opt_tag.add_argument('--tag',
#                          help="Taiga tag to use. Defaults is to not filter which can also be achieved by giving the value '*' to this option.")
#
#     opt_project_id = argparse.ArgumentParser(add_help=False)
#     opt_project_id.add_argument('--project-id', help="Project ID in Taiga to get data from.")
#
#     opt_output_path = argparse.ArgumentParser(add_help=False)
#     opt_output_path.add_argument('--output-path', help="Store daily statistics for later usage with the 'cfd' command.")
#
#     opt_target_date = argparse.ArgumentParser(add_help=False)
#     opt_target_date.add_argument('--target-date-and-layer', nargs=2,
#                                  help="Specify the targeted finish date for the project and a line for the ideal work pace will be drawn. Also specify which layer to draw the line to. e;g; \"2015-10-21 3\"")
#
#     opt_status_ids = argparse.ArgumentParser(add_help=False)
#     opt_status_ids.add_argument('--status-ids',
#                                 help="A comma separated and sorted list of User Story status IDs to use.")
#
#     opt_annotations_off = argparse.ArgumentParser(add_help=False)
#     opt_annotations_off.add_argument('--annotations-off', dest='annotations_off', action='store_true',
#                                      help="Turn off user user defined annotations. Default is on.")
#
#     opt_print_tags = argparse.ArgumentParser(add_help=False)
#     opt_print_tags.add_argument('--print-tags', dest='print_tags', action='store_true',
#                                 help="Print a US's tags in the nodes.")
#
#     opt_print_points = argparse.ArgumentParser(add_help=False)
#     opt_print_points.add_argument('--print-points', dest='print_points', action='store_true',
#                                   help="Print a US's total points in the nodes.")
#
#     # Commands
#     subparsers = parser.add_subparsers(help='Commands. Run $(taiga-stats <command> -h) for more info about a command.',
#                                        dest='command')
#     subparsers.required = True
#
#     parser_config_template = subparsers.add_parser('config_template', parents=[opt_output_path],
#                                                    help="Generate a template configuration file.")
#     parser_list_projects = subparsers.add_parser('list_projects',
#                                                  help="List all found project IDs and names on the server that you have access to read.")
#     parser_list_us_statuses = subparsers.add_parser('list_us_statuses', parents=[opt_project_id],
#                                                     help="List all the ID and names of User Story statuses.")
#     parser_burnup = subparsers.add_parser('burnup', parents=[opt_project_id, opt_tag, opt_status_ids],
#                                           help="Print burn(up|down) statistics. Typically used for entering in an Excel sheet or such that plots a burnup.", )
#     parser_store_daily = subparsers.add_parser('store_daily', parents=[opt_project_id, opt_tag, opt_output_path],
#                                                help="Store the current state of a project on file so that the CFD command can generate a diagram with this data.")
#     parser_points_sum = subparsers.add_parser('points_sum', parents=[opt_project_id, opt_tag, opt_status_ids],
#                                               help="Print out the sum of points in User Story statuses.")
#     parser_cfd = subparsers.add_parser('cfd', parents=[opt_project_id, opt_tag, opt_output_path, opt_target_date,
#                                                        opt_status_ids, opt_annotations_off],
#                                        help="Generate a Cumulative Flow Diagram from stored data.")
#     parser_deps = subparsers.add_parser('deps_dot_nodes', parents=[opt_project_id, opt_tag, opt_status_ids],
#                                         help="Print User Story nodes in .dot file format.")
#     parser_deps_dot = subparsers.add_parser('deps_dot',
#                                             parents=[opt_project_id, opt_tag, opt_output_path, opt_status_ids,
#                                                      opt_print_tags, opt_print_points],
#                                             help="Print US in .dot file format with dependencies too! Create a custom attribute for User Stories named '{:s}' by going to Settings>Attributes>Custom Fields. Then go to a User Story and put in a comma separated list of stories that this story depends on e.g. '#123,#456'.".format(
#                                                 CUST_ATTRIB_DEPENDSON_NAME))
#
#     return vars(parser.parse_args())


def main(args):
    # считываем с файла url нашего API и auth_token
    cnf_url, cnf_auth_token = read_config()
    args['url'] = args['url'] if 'url' in args and args['url'] else cnf_url
    args['auth_token'] = args['auth_token'] if 'auth_token' in args and args[
        'auth_token'] else cnf_auth_token if cnf_auth_token else None
    args['project_id'] = args['project_id'] if 'project_id' in args and args[
        'project_id'] else None
    args['tag'] = args['tag'] if 'tag' in args and args['tag'] else TAG_MATCH_ALL
    args['output_path'] = args['output_path'] if 'output_path' in args and args[
        'output_path'] else "."
    args['target_date'] = args['target_date_and_layer'][0] if 'target_date_and_layer' in args and args[
        'target_date_and_layer'] else None
    args['target_layer'] = args['target_date_and_layer'][1] if 'target_date_and_layer' in args and args[
        'target_date_and_layer'] else None
    args['status_ids'] = args['status_ids'] if 'status_ids' in args and args[
        'status_ids'] else None
    args['annotations_off'] = args['annotations_off'] if 'annotations_off' in args and args[
        'annotations_off'] is not None else False
    args['print_tags'] = args['print_tags'] if 'print_tags' in args and args['print_tags'] is not None and args[
        'print_tags'] else False
    args['print_points'] = args['print_points'] if 'print_points' in args and args['print_points'] is not None and args[
        'print_points'] else False
    # объект класса TaigaAPI
    api = taiga.TaigaAPI(host=args['url'], token=args['auth_token'])

    # получаем список всех проектов с id-шниками
    projects = api.projects.list()
    if args['command'] == 'store_daily':
        command_func = COMMAND2FUNC[args['command']]
        args.pop('command')
        for elem in projects:
            id = vars(elem)['id']
            args['project_id'] = id
            command_func(args)
    elif args['command'] == 'cfd':
        command_func = COMMAND2FUNC[args['command']]
        args.pop('command')
        for elem in projects:
            id = vars(elem)['id']
            name = vars(elem)['name']
            args['project_id'] = id
            args['project_name'] = name
            command_func(args)
    elif args['command'] == 'deps_dot':
        command_func = COMMAND2FUNC[args['command']]
        args.pop('command')
        for elem in projects:
            id = vars(elem)['id']
            args['project_id'] = id
            command_func(args)
    elif args['command'] == 'deps_gen':
        command_func = COMMAND2FUNC[args['command']]
        args.pop('command')
        for elem in projects:
            id = vars(elem)['id']
            dataPath = './deps_dat/dependencies_%s.dot' % str(id)
            if os.path.isfile(dataPath):
                command_func(dataPath, MEDIA_ROOT + '/agile_stats_snapshots/dot/dependencies_project_%s.png' % str(id))
    elif args['command'] == 'burnup':
        command_func = COMMAND2FUNC[args['command']]
        args.pop('command')
        for elem in projects:
            id = vars(elem)['id']
            name = vars(elem)['name']
            args['project_id'] = id
            args['project_name'] = name
            command_func(args)
    elif args['command'] == 'velocity':
        command_func = COMMAND2FUNC[args['command']]
        args.pop('command')
        for elem in projects:
            id = vars(elem)['id']
            args['project_id'] = id
            command_func(args)
    elif args['command'] not in COMMAND2FUNC:
        print("Misconfiguration for argparse: subcommand not mapped to a function")
        return 1
    # command_func = COMMAND2FUNC[args['command']]
    # args.pop('command')
    # return command_func(args)
