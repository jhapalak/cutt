#
# cutt: Create readable timetables for Chandigarh University.
# Copyright (C) 2021 Palak Kumar Jha <palakjha.dev@gmail.com>
# Licensed under the GNU GPL version 3.
#

__all__ = [
    'timetable',
    'cmd_courseinfo',
    'cmd_gsheet',
    'cmd_csv',
    'cutt',
]

import json
import csv
import pickle
import time
import argparse
from textwrap import dedent as d
from os import path


def timetable(raw_data, courseinfo=None):
    raw_tt, raw_courseinfo = _raw_data_split(raw_data)
    courseinfo = courseinfo or _courseinfo_processed(raw_courseinfo)
    tt = _timetable_processed(raw_tt, courseinfo)
    return tt


def _courseinfo_processed(raw_courseinfo):
    return dict(raw_courseinfo)


def _timetable_from_files(timetable_filepath, courseinfo_filepath):
    with open(timetable_filepath, 'r') as tf, \
         open(courseinfo_filepath, 'r') as cf:
        return timetable(list(csv.reader(tf)), json.load(cf))


def _raw_data_split(raw_data):
    separator_index = raw_data.index([])
    raw_timetable = raw_data[1:separator_index]
    raw_courseinfo = raw_data[separator_index+2:-1]
    return raw_timetable, raw_courseinfo


_BREAK_PERIOD = ''

def _timetable_processed(raw_tt, courseinfo):

    def fmt_duration(d):
        d = d.strip()
        start, _, end, _ = d.split()
        def fmt_time(t):
            hrs, mins = t.split(':')
            return f'{hrs.zfill(2)}:{mins.zfill(2)}'
        return f'{fmt_time(start)}-{fmt_time(end)}'

    def fmt_weekday(w):
        return w.strip().title()

    def fmt_courseinfo(c):
        if c == _BREAK_PERIOD:
            return '---'
        code = c[:c.find(':')]
        return courseinfo[code]

    d = {}
    for duration, _, course in raw_tt:
        duration = fmt_duration(duration)
        course = fmt_courseinfo(course)
        row = d.setdefault(duration, [])
        row.append(course)

    weekdays = list(map(fmt_weekday, _working_weekdays(raw_tt)))
    tt = [['Timings'] + weekdays]
    for k, v in d.items():
        tt.append([k]+v)

    return tt


def _working_weekdays(raw_tt):
    weekdays = []
    for _, wd, _ in raw_tt:
        if wd in weekdays:
            break
        weekdays.append(wd)
    return weekdays


def _google_spreadsheet(token_filepath,
                        credentials_filepath,
                        timetable,
                        title,
                        should_prettify,
                        ):
    s = _google_service(token_filepath, credentials_filepath)
    spreadsheet_id = _google_spreadsheet_new(s, title)
    _google_spreadsheet_fill(s, spreadsheet_id, timetable)
    if should_prettify:
        _google_spreadsheet_prettify(s, spreadsheet_id, timetable)
    return spreadsheet_id


_GOOGLE_API_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
]

# Taken from https://developers.google.com/sheets/api/quickstart/python
def _google_service(token_filepath, credentials_filepath):
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    token = None
    if path.exists(token_filepath):
        with open(token_filepath, 'rb') as f:
            token = pickle.load(f)
    if not token or not token.valid:
        if token and token.expired and token.refresh_token:
            token.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_filepath,
                _GOOGLE_API_SCOPES,
            )
            token = flow.run_local_server(port=0)
        with open(token_filepath, 'wb') as f:
            pickle.dump(token, f)
    return build('sheets', 'v4', credentials=token)


def _google_spreadsheet_new(service, title):
    request = {'properties': {'title': title}}
    response = service.spreadsheets().create(
        body=request,
    ).execute()
    return response['spreadsheetId']


def _google_spreadsheet_fill(service, spreadsheet_id, timetable):
    request = {'values': timetable}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='A1',
        body=request,
        valueInputOption='RAW',
    ).execute()


def _google_spreadsheet_prettify(service, spreadsheet_id, timetable):
    requests = _google_spreadsheet_prettifying_requests(timetable)
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=requests,
    ).execute()


def _google_color(r, g, b, a):
    return {'red': r, 'green': g, 'blue': b, 'alpha': a}

_GOOGLE_COLOR_WHITE = _google_color(1, 1, 1, 1)
_GOOGLE_COLOR_BLUE = _google_color(0.447, 0.478, 0.993, 1)
_GOOGLE_COLOR_LIGHT_BLUE = _google_color(0.894, 0.925, 0.984, 1)


def _google_spreadsheet_prettifying_requests(timetable):
    end_row_index = len(timetable)
    end_column_index = len(timetable[0])
    full_range = {
        'endRowIndex': end_row_index,
        'endColumnIndex': end_column_index,
    }

    return {
        'requests': [
            # Base formatting; common to all cells
            {
                'repeatCell': {
                    'range': full_range,
                    'cell': {
                        'userEnteredFormat': {
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'MIDDLE',
                            'wrapStrategy': 'WRAP',
                        },
                    },
                    'fields': '''userEnteredFormat(\
                                    horizontalAlignment,\
                                    verticalAlignment,\
                                    wrapStrategy,\
                                    )''',
                },
            },
            # Alternating row colours
            {
                'addBanding': {
                    'bandedRange': {
                        'range': full_range,
                        'rowProperties': {
                            'headerColor': _GOOGLE_COLOR_BLUE,
                            'firstBandColor': _GOOGLE_COLOR_LIGHT_BLUE,
                            'secondBandColor': _GOOGLE_COLOR_WHITE,
                        },
                    },
                },
            },
            # Header formatting
            {
                'repeatCell': {
                    'range': {
                        'endRowIndex': 1,
                        'endColumnIndex': end_column_index,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'foregroundColor': _GOOGLE_COLOR_WHITE,
                                'bold': True,
                            },
                        },
                    },
                    'fields': '''userEnteredFormat.textFormat(\
                                    foregroundColor,\
                                    bold)''',
                },
            },
            # Timings column formatting
            {
                'repeatCell': {
                    'range': {
                        'startRowIndex': 1,  # Don't touch the header
                        'endRowIndex': end_row_index,
                        'endColumnIndex': 1,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                            },
                        },
                    },
                    'fields': 'userEnteredFormat.textFormat.bold',
                },
            },
        ]
    }


_DEFAULT_FILEPATH_COURSEINFO = 'courseinfo.json'
_DEFAULT_FILEPATH_TOKEN = 'token.pickle'
_DEFAULT_FILEPATH_CREDENTIALS = 'credentials.json'
_DEFAULT_FILEPATH_OUTPUT_CSV = 'a.csv'


_DEFAULT_TITLE_FORMAT = 'cutt-{timestamp}'

def _default_title(fmt=_DEFAULT_TITLE_FORMAT):
    timestamp = time.strftime('%d%b%Y-%I%M%p')
    return fmt.format(timestamp=timestamp)


_COMMON_OPTION_HELP_TIMETABLE = d('''\
    Path to .csv file containing the timetable (required).
    You can download it from CUIMS (university's website).''')
_COMMON_OPTION_HELP_COURSEINFO = d('''\
    Path to .json file containing course information.
    If not specified, "{}" is assumed.''')\
    .format(_DEFAULT_FILEPATH_COURSEINFO)


def _set_subparser_args_handler(subparser, handler):
    subparser.set_defaults(args_handler=handler)


def cmd_gsheet(timetable_filepath,
               courseinfo_filepath=None,
               token_filepath=None,
               credentials_filepath=None,
               title=None,
               plain=False,
               ):
    tt = _timetable_from_files(
        timetable_filepath,
        courseinfo_filepath or _DEFAULT_FILEPATH_COURSEINFO,
    )
    spreadsheet_id = _google_spreadsheet(
        token_filepath or _DEFAULT_FILEPATH_TOKEN,
        credentials_filepath or _DEFAULT_FILEPATH_CREDENTIALS,
        tt,
        title or _default_title(),
        not plain,
    )
    return spreadsheet_id


def _add_parser_cmd_gsheet(subparsers):
    parser = subparsers.add_parser(
        'gsheet',
        formatter_class=argparse.RawTextHelpFormatter,
        help='Create a Google Sheet')

    parser.add_argument(
        'timetable',
        help=_COMMON_OPTION_HELP_TIMETABLE)
    parser.add_argument(
        '-c', '--courseinfo',
        help=_COMMON_OPTION_HELP_COURSEINFO)
    parser.add_argument(
        '-t', '--title',
        help=d('''\
            Title for the Google Sheet.
            If not specified, a timestamped default is used.
            Default title format: "{}".''')
            .format(_DEFAULT_TITLE_FORMAT))
    parser.add_argument(
        '-p', '--plain',
        action='store_true',
        help=d('''\
            Write only plain text to Google Sheet.
            Don't prettify.'''))
    parser.add_argument(
        '--token',
        help=d('''\
            Path to .pickle file containing the Google API token.
            If not specified, "{}" is assumed.''')
            .format(_DEFAULT_FILEPATH_TOKEN))
    parser.add_argument(
        '--credentials',
        help=d('''\
            Path to .json file containing the Google API credentials.
            If not specified, "{}" is assumed.''')
            .format(_DEFAULT_FILEPATH_CREDENTIALS))

    def args_handler(args):
        cmd_gsheet(
            args.timetable,
            args.courseinfo,
            args.token,
            args.credentials,
            args.title,
            args.plain,
        )

    _set_subparser_args_handler(parser, args_handler)


def cmd_csv(timetable_filepath,
            output_filepath=None,
            courseinfo_filepath=None,
            ):
    tt = _timetable_from_files(
        timetable_filepath,
        courseinfo_filepath or _DEFAULT_FILEPATH_COURSEINFO,
    )
    _csv_create_file(
        output_filepath or _DEFAULT_FILEPATH_OUTPUT_CSV,
        tt,
    )


def _csv_create_file(destination_filepath, rows):
    with open(destination_filepath, 'w') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerows(rows)


def _add_parser_cmd_csv(subparsers):
    parser = subparsers.add_parser(
        'csv',
        formatter_class=argparse.RawTextHelpFormatter,
        help='Output a CSV file')

    parser.add_argument(
        'timetable',
        help=_COMMON_OPTION_HELP_TIMETABLE)
    parser.add_argument(
        '-o', '--output',
        help=d('''\
            Place output into this file.
            If not specified, "{}" is assumed.''')
            .format(_DEFAULT_FILEPATH_OUTPUT_CSV))
    parser.add_argument(
        '-c', '--courseinfo',
        help=_COMMON_OPTION_HELP_COURSEINFO)

    def args_handler(args):
        cmd_csv(
            args.timetable,
            args.output,
            args.courseinfo,
        )

    _set_subparser_args_handler(parser, args_handler)


def cmd_courseinfo(timetable_filepath,
                   output_filepath=None,
                   interactive=False,
                   ):
    courseinfo = _courseinfo_from_file(timetable_filepath)
    if interactive:
        _courseinfo_interactive_edit(courseinfo)
    _courseinfo_create_file(
        courseinfo,
        output_filepath or _DEFAULT_FILEPATH_COURSEINFO,
    )


def _courseinfo_from_file(timetable_filepath):
    with open(timetable_filepath, 'r') as f:
        raw_data = list(csv.reader(f))
    _, raw_courseinfo = _raw_data_split(raw_data)
    return _courseinfo_processed(raw_courseinfo)


def _courseinfo_interactive_edit(courseinfo):
    print(d('''\
        Enter alternative names for courses as prompted.
        If no alternative name is given, the default name is kept.
        Recommendation: Keep names shorter than 11 characters.
        '''))
    items = sorted(courseinfo.items(), key=lambda x: x[1])
    for k, v in items:
        newname = input(f'Alternative name for "{v}" = ').strip()
        if newname:
            courseinfo[k] = newname
    return courseinfo


def _courseinfo_create_file(courseinfo, filepath):
    with open(filepath, 'w') as f:
        json.dump(courseinfo, f, indent='\t')


def _add_parser_cmd_courseinfo(subparsers):
    parser = subparsers.add_parser(
        'courseinfo',
        aliases=['ci'],
        formatter_class=argparse.RawTextHelpFormatter,
        help='Generate course-related information (required)')

    parser.add_argument(
        'timetable',
        help=_COMMON_OPTION_HELP_TIMETABLE)
    parser.add_argument(
        '-o', '--output',
        help=d('''\
            Place output into this file.
            If not specified, "{}" is assumed''')
            .format(_DEFAULT_FILEPATH_COURSEINFO))
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactively create the file.')

    def args_handler(args):
        cmd_courseinfo(
            args.timetable,
            args.output,
            args.interactive,
        )

    _set_subparser_args_handler(parser, args_handler)


def cutt(args=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(title='Sub-commands')

    _add_parser_cmd_courseinfo(subparsers)
    _add_parser_cmd_csv(subparsers)
    _add_parser_cmd_gsheet(subparsers)

    namespace = parser.parse_args(args)
    if not hasattr(namespace, 'args_handler'):
        parser.error('Must either pass an option or use a subcommand.')
    namespace.args_handler(namespace)


if __name__ == '__main__':
    cutt()
