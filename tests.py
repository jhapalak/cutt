import unittest
import io
import csv

import cutt


def the_test_data():
    TIMINGS = 'Timings'
    BREAK = '---'
    the_data = {
        (2, 2, 0): (
            [
                ['TimingId', 'DayNo', 'CourseCode'],
                ['a0:a0 - a0:a0 A0', 'Aaa', '00AAA-000:'],
                [],
                ['CourseCode1', 'Title'],
                ['00AAA-000', 'a0a0'],
                []
            ],
            {
                '00AAA-000': '*a0a0*'
            },
            [
                [TIMINGS, 'Aaa'],
                ['a0:a0-a0:a0', 'a0a0']
            ],
            [
                [TIMINGS, 'Aaa'],
                ['a0:a0-a0:a0', '*a0a0*']
            ]
        ),
        (2, 2, 1): (
            [
                ['TimingId', 'DayNo', 'CourseCode'],
                ['a0:a0 - a0:a0 A0', 'Aaa', ''],
                [],
                ['CourseCode1', 'Title'],
                ['00AAA-000', 'a0a0'],
                []
            ],
            {
                '00AAA-000': '*a0a0*'
            },
            [
                [TIMINGS, 'Aaa'],
                ['a0:a0-a0:a0', BREAK]
            ],
            [
                [TIMINGS, 'Aaa'],
                ['a0:a0-a0:a0', BREAK]
            ]
        ),
        (2, 3, 0): (
            [
                ['TimingId', 'DayNo', 'CourseCode'],
                ['a0:a0 - a0:a0 A0', 'Aaa', '00AAA-000:'],
                ['a0:a0 - a0:a0 A0', 'Bbb', '00BBB-000:'],
                [],
                ['CourseCode1', 'Title'],
                ['00AAA-000', 'a0a0'],
                ['00BBB-000', 'b0b0'],
                []
            ],
            {
                '00AAA-000': '*a0a0*',
                '00BBB-000': '*b0b0*'
            },
            [
                [TIMINGS, 'Aaa', 'Bbb'],
                ['a0:a0-a0:a0', 'a0a0', 'b0b0']
            ],
            [
                [TIMINGS, 'Aaa'],
                ['a0:a0-a0:a0', '*a0a0*', '*b0b0*']
            ]
        ),
        (3, 2, 0): (
            [
                ['TimingId', 'DayNo', 'CourseCode'],
                ['a0:a0 - a0:a0 A0', 'Aaa', '00AAA-000:'],
                ['a1:a1 - a1:a1 A1', 'Aaa', '11AAA-111:']
                [],
                ['CourseCode1', 'Title'],
                ['00AAA-000', 'a0a0'],
                ['11AAA-111', 'a1a1'],
                []
            ],
            {
                '00AAA-000': '*a0a0*',
                '11AAA-111': '*a1a1*'
            },
            [
                [TIMINGS, 'Aaa'],
                ['a0:a0-a0:a0', 'a0a0'],
                ['a1:a1-a1:a1', 'a1a1']
            ],
            [
                [TIMINGS, 'Aaa'],
                ['a0:a0-a0:a0', '*a0a0*']
                ['a1:a1-a1:a1', '*a1a1*'],
            ]
        ),
    }
    return the_data.items()


class TimetableTestCase(unittest.TestCase):
    def test_coursetable_extraction(self):
        for id, (rawdata, _, timetable, _) in the_test_data():
            with self.subTest(id=id):
                self.assertEqual(cutt.timetable(rawdata), timetable)

    def test_given_coursetable_usage(self):
        for id, (rawdata, coursetable, _, custom_timetable) in the_test_data():
            with self.subTest(id=id):
                self.assertEqual(cutt.timetable(rawdata, coursetable),
                                 custom_timetable)

    def test_multiple_vacant_periods_in_a_day(self):
        rawdata = [
            ['TimingId', 'DayNo', 'CourseCode'],
            ['a0:a0 - a0:a0 A0', 'Aaa', ''],
            ['a1:a1 - a1:a1 A1', 'Aaa', '']
            [],
            ['CourseCode1', 'Title'],
            ['00AAA-000', 'a0a0'],
            ['11AAA-111', 'a1a1'],
            []
        ]
        expected = [
            [TIMINGS, 'Aaa'],
            ['a0:a0-a0:a0', BREAK],
            ['a1:a1-a1:a1', BREAK]
        ]
        output = cutt.timetable(rawdata)
        self.assertEqual(output, expected)

    def test_timings_zero_fill(self):
        rawdata = [
            ['TimingId', 'DayNo', 'CourseCode'],
            ['0:0 - 0:0 A0', 'Aaa', '00AAA-000:'],
            [],
            ['CourseCode1', 'Title'],
            ['00AAA-000', 'a0a0'],
            []
        ]
        expected = [
            [TIMINGS, 'Aaa'],
            ['00:00-00:00', 'a0a0']
        ]
        output = cutt.timetable(rawdata)
        self.assertEqual(output, expected)


class CoursetableTestCase(unittest.TestCase):
    def test(self):
        for id, (rawdata, coursetable, _, _) in the_test_data():
            with self.subTest(id=id):
                self.assertEqual(cutt.coursetable(rawdata), coursetable)


class CsvTestCase(unittest.TestCase):
    def matrix_to_csv(self, timetable):
        sio = io.StringIO()
        csv.writer(sio).writerows(timetable)
        return sio.getvalue()

    def assertCorrectCsvGenerated(self, timetable):
        sio = io.StringIO()
        cutt.csv(timetable, sio)
        output = sio.getvalue()
        expected = self.matrix_to_csv(timetable)
        self.assertEqual(output, expected)

    def test_with_default_timetable(self):
        for id, (_, _, timetable, _) in the_test_data():
            with self.subTest(id=id):
                self.assertCorrectCsvGenerated(timetable)

    def test_with_custom_timetable(self):
        for id, (_, _, _, custom_timetable) in the_test_data():
            with self.subTest(id=id):
                self.assertCorrectCsvGenerated(custom_timetable)


@unittest.skip('TODO')
class GsheetTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
