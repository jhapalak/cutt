# A client config file is required for this to work. You can get it
# here: https://developers.google.com/sheets/api/quickstart/python

import csv, json, pickle
import time
import argparse
import textwrap
from os import path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


should_log = True

def log(msg):
    if should_log:
        print(msg)


# An empty line separates the actual timetable from the subject info in
# the CSV file obtained from CUIMS. That empty line shows up as an
# empty list after the file-obj is passed through csv.reader().
SEPARATOR = []

def raw_data(filepath):
    """Return the raw timetable and coursenames table from the CSV."""
    log(f'Reading data from {filepath}')

    with open(filepath, 'r') as f:
        schedule = list(csv.reader(f))
    separator_index = schedule.index(SEPARATOR)
    # The slice bounds are chosen as such since that's how the data
    # is arranged in the CSV file.
    tt = schedule[1:separator_index]
    cnames = schedule[separator_index+2:-1]
    return tt, cnames


def coursenames_table(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


TOP_LEFT_CELL_TEXT = 'Timings'
BREAK_PERIOD = 'BREAK'

def transformed_timetable(raw_tt, coursenames_table):
    """Correct the raw timetable's structure into the more familiar
    Weekday*Duration grid form. Also, format its contents."""
    log('Processing data...')

    def fmt_duration(d):
        # Convert the duration, as in the raw timetable, to the form
        # 'HH:MM-HH:MM'.
        d = d.strip()
        start, _, end, _ = d.split()
        def fmt_time(t):
            h, m = t.split(':')
            return f'{h.zfill(2)}:{m.zfill(2)}'
        return f'{fmt_time(start)}-{fmt_time(end)}'

    def fmt_weekday(wd):
        return wd.strip().title()
    
    def fmt_courseinfo(ci):
        code = ci[:ci.find(':')] if ci else BREAK_PERIOD
        return coursenames_table[code]

    weekdays = list(map(fmt_weekday, get_working_weekdays(raw_tt)))

    tt = {}
    for duration, _, courseinfo in raw_tt:
        duration = fmt_duration(duration)
        courseinfo = fmt_courseinfo(courseinfo)
        row = tt.setdefault(duration, [])
        row.append(courseinfo)

    grid = [[TOP_LEFT_CELL_TEXT] + weekdays]
    for k, v in tt.items():
        grid.append([k]+v)

    return grid


# Reality is unpredictable. That Saturdays will be off is not guaranteed.
# There may be other such exceptions too. So, actually look at the data
# and list the working weekdays.
def get_working_weekdays(raw_tt):
    """Return a list of strings representing the working weekdays as
    obtained from the actual raw timetable."""
    weekdays = []
    for _, wd, _ in raw_tt:
        if wd in weekdays:
            break
        weekdays.append(wd)
    return weekdays


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
TOKEN_FILEPATH = 'token.pickle'
CREDENTIALS_FILEPATH = 'credentials.json'

# Taken from https://developers.google.com/sheets/api/quickstart/python
def service():
    log('Doing some network stuff...')

    creds = None
    if path.exists(TOKEN_FILEPATH):
        with open(TOKEN_FILEPATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILEPATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILEPATH, 'wb') as token:
            pickle.dump(creds, token)
    return build('sheets', 'v4', credentials=creds)


def get_formatting_request(timetable):
    end_row_index = len(timetable)
    end_column_index = len(timetable[0])

    return {
        'requests': [
            # Basic formatting common to all cells
            {
                'repeatCell': {
                    'range': {
                        'endRowIndex': end_row_index,
                        'endColumnIndex': end_column_index,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'MIDDLE',
                            'wrapStrategy': 'WRAP',
                            'textFormat': {
                                'fontSize': 10,
                                'bold': False,
                                'fontFamily': 'Merriweather',
                            },
                        },
                    },
                    'fields': 'userEnteredFormat(horizontalAlignment,verticalAlignment,textFormat,wrapStrategy)'
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
                            'horizontalAlignment': 'CENTER',
                            'textFormat': {
                                'foregroundColor': {
                                    'red': 1,
                                    'green': 1,
                                    'blue': 1,
                                    'alpha': 1,
                                },
                                'fontSize': 10,
                                'bold': True,
                                'fontFamily': 'Merriweather',
                            },
                        },
                    },
                    'fields': 'userEnteredFormat(horizontalAlignment,textFormat)'
                },
            },
            # First column formatting
            {
                'repeatCell': {
                    'range': {
                        'startRowIndex': 1,  # Don't format the header
                        'endRowIndex': end_row_index,
                        'endColumnIndex': 1,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'horizontalAlignment': 'CENTER',
                            'textFormat': {
                                'foregroundColor': {
                                    'red': 0,
                                    'green': 0,
                                    'blue': 0,
                                    'alpha': 1,
                                },
                                'fontSize': 10,
                                'bold': True,
                                'fontFamily': 'Merriweather',
                            },
                        },
                    },
                    'fields': 'userEnteredFormat(horizontalAlignment,textFormat)'
                },
            },
            # Alternating row colours
            {
                'addBanding': {
                    'bandedRange': {
                        'range': {
                            'endRowIndex': end_row_index,
                            'endColumnIndex': end_column_index,
                        },
                        'rowProperties': {
                            'headerColor': {
                                'red': 0.447,
                                'green': 0.478,
                                'blue': 0.993,
                                'alpha': 1,
                            },
                            'firstBandColor': {
                                'red': 0.894,
                                'green': 0.925,
                                'blue': 0.984,
                                'alpha': 1,
                            },
                            'secondBandColor': {
                                'red': 1,
                                'green': 1,
                                'blue': 1,
                                'alpha': 1,
                            },
                        },
                    },
                },
            },
        ]
    }


def make_spreadsheet(service, title, timetable):
    log(f'Creating spreadsheet...')

    # Create spreadsheet
    response = service.spreadsheets().create(
        body={'properties': {'title': title}}).execute()
    ssid = response['spreadsheetId']

    # Write data to it
    service.spreadsheets().values().update(
        spreadsheetId=ssid, range='A1',
        body={'values': timetable},
        valueInputOption='RAW').execute()

    return ssid


def format_spreadsheet(service, ssid, fmt_request):
    log('Formatting spreadsheet...')

    service.spreadsheets().batchUpdate(
        spreadsheetId=ssid, body=fmt_request
    ).execute()


DEFAULT_TITLE_FORMAT = 'CU-Timetable-{timestamp}'

def default_title():
    """Return a timestamped title."""
    timestamp = time.strftime('%d%b%Y-%I%M%p')
    return DEFAULT_TITLE_FORMAT.format(timestamp=timestamp)


def make_default_coursenames_file(cnames, filepath):
    log('Creating default coursenames file...')

    table = dict(cnames)
    table[BREAK_PERIOD] = '---'
    with open(filepath, 'w') as f:
        json.dump(table, f, indent='\t')


DEFAULT_COURSENAMES_TABLE_FILEPATH = 'coursenames.json'

def cu_timetable(
    timetable_filepath,
    coursenames_filepath=None,
    title=None,
    should_format=True,
    verbose=True,
):
    global should_log
    should_log = verbose

    log('Starting...')

    raw_tt, raw_cnames_table = raw_data(timetable_filepath)

    if coursenames_filepath:
        cnames = coursenames_table(coursenames_filepath)
    else:
        if not path.exists(DEFAULT_COURSENAMES_TABLE_FILEPATH):
            make_default_coursenames_file(
                raw_cnames_table,
                DEFAULT_COURSENAMES_TABLE_FILEPATH)
        cnames = coursenames_table(DEFAULT_COURSENAMES_TABLE_FILEPATH)

    tt = transformed_timetable(raw_tt, cnames)
    title = title or default_title()
    serv = service()
    ssid = make_spreadsheet(serv, title, tt)

    if should_format:
        format_spreadsheet(serv, ssid, get_formatting_request(tt))

    log(f'Timetable saved to your Google Drive as "{title}".')


def main(args=None):
    d = textwrap.dedent

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=d("""\
            Program to prettify and make readable the overwhelmingly info-dense
            timetables provided on CUIMS (university's website)."""))

    parser.add_argument(
        "timetable",
        help=d("""\
            Path to CSV file containing the timetable. You can
            download it from CUIMS (university's website)."""))

    parser.add_argument(
        "-c", "--coursenames",
        help=d("""\
            Path to JSON file containing the CourseId->CourseName
            mapping. If not specified, the default "{}"
            is assumed. If the default doesn't exist, it is generated
            based on the information in the CSV file <timetable>.
            You may edit the default file if you want to change the
            display text for courses. You must not edit the course
            codes.""").format(DEFAULT_COURSENAMES_TABLE_FILEPATH))
    parser.add_argument(
        "-t", "--title",
        help=d("""\
            Title for the google sheet containing the timetable.
            If not specified, a timestamped default title is used.
            Default title format: "{}".""".format(DEFAULT_TITLE_FORMAT)))
    parser.add_argument(
        "-p", "--plain",
        action="store_true",
        help="Write only plain text to google sheet--don't prettify/format.")
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help=d("""\
            Don't report progress to output stream. This doesn't suppress
            errors."""))

    ns = parser.parse_args(args)
    cu_timetable(
        ns.timetable,
        ns.coursenames,
        ns.title,
        not ns.plain,
        not ns.quiet,
    )


if __name__ == '__main__':
    main()
