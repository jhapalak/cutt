#
# A quick sanity check for cutt.timetable(). Not even close to
# sufficient, and quite brittle too, but will do for now.
#

import unittest
import json
import io
import cutt


raw_timetable_1 = """\
foo,foo,foo
00:00 - 00:00 bar,Day0,code0:T:: Gp-X:foobarspam
00:00 - 00:00 bar,Day1,code2:T:: Gp-X:foobarspam
11:11 - 11:11 bar,Day0,
11:11 - 11:11 bar,Day1,
22:22 - 22:22 bar,Day0,code1:T:: Gp-X:foobarspam
22:22 - 22:22 bar,Day1,code0:T:: Gp-X:foobarspam

spam,spam
code0,course0
code1,course1
code2,course2
"""
courseinfo_json_1 = json.dumps(
    {
        'code0': 'course0',
        'code1': 'course1',
        'code2': 'course2'
    }
)
expected_processed_timetable_1 = [
    ['Timings',     'Day0',     'Day1'],
    ['00:00-00:00', 'course0',  'course2'],
    ['11:11-11:11', '---',      '---'],
    ['22:22-22:22', 'course1',  'course0'],
]


class TimetableTestCase(unittest.TestCase):

    def test_timetable_sanity(self):
        stream_timetable = io.StringIO(raw_timetable_1)
        stream_courseinfo = io.StringIO(courseinfo_json_1)
        self.assertEqual(
            cutt.timetable(stream_timetable, stream_courseinfo),
            expected_processed_timetable_1
        )


if __name__ == '__main__':
    unittest.main()
