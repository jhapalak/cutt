=============
API Reference
=============

Like all good command line scripts, ``cutt`` also exposes an API for
programmatic access. The functions constituting this API are mostly
similar to their command line counterparts. Slight differences exist,
however,  since the command line interface doesn't always make sense
as an API, nor is it always as testable.

The Functions
=============

.. function:: cutt.cutt(args=None)

	This is the boss function. It executes the program with the
	given command line arguments as if they were passed to ``cutt``
	via the shell.

	*args:* A list of strings; the command line arguments. Defaults
	to ``None``, in which case ``sys.argv`` is appropriately used.

	For example, the following command line call:

	::

		$ python -m cutt --help

	is equivalent to the following Python function call:

	::

		>>> cutt.cutt(['--help'])

.. function:: cutt.timetable(raw_data, courseinfo=None)

	Returns a timetable as a two-dimensional list of strings. Its
	structure is as follows:

	::

		[['Timings', 'Mon', 'Tue', ...],
		 ['10:00-10:45', 'coursename-1', 'coursename-2', ...],
		 ['11:00-11:45', 'coursename-3', 'coursename-1', ...],
		 ...]

	*raw_data:* The contents of the CSV file downloaded from the
	university's website (CUIMS) but after the file object is passed
	through ``list(csv.reader())``.

	*courseinfo:* A dictionary of ``course-id, course-name`` pairs.
	Defaults to ``None``, in which case the coursenames are extracted
	from the previous argument ``raw_data``.

.. function:: cutt.cmd_courseinfo()
.. function:: cutt.cmd_csv()
.. function:: cutt.cmd_gsheet()
