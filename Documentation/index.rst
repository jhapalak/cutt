=========================================
Documentation for CU-Timetable (``cutt``)
=========================================

CU-Timetable or ``cutt`` is a command line script that generates readable
timetables for the students of Chandigarh University.

The Problem: Timetable, why you hate me?
========================================
The timetables provided on the university's website are hard to read. For
example, here's a screenshot of a timetable as seen on the university's
website:

.. TODO add a picture here

Quick question: Where do you see the course names *in the timetable*?

That's right, course names are nowhere to be seen in the timetable proper. You
are given instead the course IDs. You then have to find the corresponding
course names from the table at the bottom. Ah, how convenient!

The Solution: ``cutt`` saves the day!
=====================================
Enter ``cutt``. It solves the problem by converting the unreadable timetables
to something like this sweet baby:

.. TOTO add a picture here

Awww, look how readable... and pretty! Koochee koochee koo...

Now, you can tell at a glance what the subjects for the day are. Yay!

Actual Documentation
====================
For more information, see the documents listed below:

.. toctree::
	:maxdepth: 1

	tutorial.rst
	cli-reference.rst
	api-reference.rst
	howto-add-new-subcommand.rst
