# A client config file is required for this to work. You can get it
# here: https://developers.google.com/sheets/api/quickstart/python

import csv, json, pickle, time
from os import path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# An empty line separates the actual timetable from the subject info in
# the CSV file obtained from CUIMS. That empty line shows up as an
# empty list after the file-obj is passed through csv.reader().
SEPARATOR = []

def raw_data(filepath):
    """Return the raw timetable and coursenames table from the CSV."""
    with open(filepath, 'r') as f:
        schedule = list(csv.reader(f))
    separator_index = schedule.index(SEPARATOR)
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
    endRowIndex = len(timetable)
    endColumnIndex = len(timetable[0])

    #XXX Taking up too much space. Move this to a JSON file?
    return {
        'requests': [
            # Font face
            {
                'repeatCell': {
                    'range': {
                        'endRowIndex': endRowIndex,
                        'endColumnIndex': endColumnIndex,
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'horizontalAlignment': 'CENTER',
                            'textFormat': {
                                'fontSize': 10,
                                'bold': False,
                                'fontFamily': 'Merriweather',
                            },
                        },
                    },
                    'fields': 'userEnteredFormat(horizontalAlignment,textFormat)'
                },
            },
            # Header formatting
            {
                'repeatCell': {
                    'range': {
                        'endRowIndex': 1,
                        'endColumnIndex': endColumnIndex,
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
                        'startRowIndex': 1,  # Don't include the header
                        'endRowIndex': endRowIndex,
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
                            'endRowIndex': endRowIndex,
                            'endColumnIndex': endColumnIndex,
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


#XXX Split this into three?
def make_spreadsheet(service, title, timetable):
    # Create spreadsheet
    response = service.spreadsheets().create(
        body={'properties': {'title': title}}).execute()
    ssid = response['spreadsheetId']

    # Write data to it
    service.spreadsheets().values().update(
        spreadsheetId=ssid, range='A1',
        body={'values': timetable},
        valueInputOption='RAW').execute()

    # Format sheet to a presentable form
    service.spreadsheets().batchUpdate(
        spreadsheetId=ssid, body=get_formatting_request(timetable)
    ).execute()


def default_title():
    """Return a timestamped title."""
    return 'CU-Timetable ({})'.format(time.ctime())


def cu_timetable(timetable_filepath, coursenames_filepath, title=None):
    raw_tt, _ = raw_data(timetable_filepath)
    tt = transformed_timetable(
        raw_tt,
        coursenames_table(coursenames_filepath)
    )
    title = title or default_title()
    make_spreadsheet(service(), title, tt)


if __name__ == '__main__':
    cu_timetable('tt.csv', 'coursenames.json')
