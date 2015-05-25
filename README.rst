Nereid Project
===============

.. image:: https://travis-ci.org/openlabs/nereid-project.svg?branch=develop
    :target: https://travis-ci.org/openlabs/nereid-project
    :alt: Build Status
.. image:: https://pypip.in/download/trytond_nereid-project/badge.svg
    :target:  https://pypi.python.org/pypi/trytond_nereid-project/
    :alt: Downloads
.. image:: https://pypip.in/version/trytond_nereid-project/badge.svg
    :target: https://pypi.python.org/pypi/trytond_nereid-project/
    :alt: Latest Version
.. image:: https://pypip.in/status/trytond_nereid-project/badge.svg
    :target: https://pypi.python.org/pypi/trytond_nereid-project/
    :alt: Development Status
.. image:: https://coveralls.io/repos/openlabs/nereid-project/badge.svg?branch=develop 
    :target: https://coveralls.io/r/openlabs/nereid-project?branch=develop 


A web based project management system built on the Tryton framework and
nereid.

**Nereid Project** is an open-source collaborative development platform offered
by Team Openlabs. It is mainly used for managing project processes. While it
could be used for managing any kind of projects, it is primarily used at
Openlabs to manage software projects. It is designed to help organise projects
& tasks. The aim is to connect everything together on a single interface,
avoiding unecessary time consumption, and track project's progress, task's
status, shared files, time spent on individual tasks. 

The goal of nereid project is to provide a friendly web based user interface to 
stakeholders outside the company to the powerful project management module of 
Tryton.

* Separate user accounts for users outside the company (like customers &
  freelancers) without giving access to Tryton.

* Simplify the project management tasks to encourage participation from users
  who may not be tech savvy.


Installation
============

.. code:: sh

    $ pip install trytond_nereid_project

To install from source
~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

    $ git clone git://github.com/openlabs/nereid-project.git
    $ cd nereid-project
    $ python setup.py install

API Reference
=============

/projects/
  - *GET*: Get all projects paginated response
  - *POST*: Create new project
  - *DELETE*: N/A
/projects/``:id``/
  - *GET*: Return serialized project
  - *POST*: edit project
  - *DELETE*: delete a project
/projects/``:id``/tasks/
  - *GET*: Return tasks list of project
  - *POST*: Create a task in project
  - *DELETE*: N/A
/projects/``:id``/tasks/``:id``/
  - *GET*: return serialized task
  - *POST*: edit task
  - *DELETE*: delete a task
/projects/``:id``/tasks/``:id``/move
  - *POST*: to move task to diff project.
/projects/``:id``/tasks/``:id``/watch
  - *POST*: action=watch
/projects/``:id``/tasks/``:id``/unwatch
  - *POST*: action=unwatch
/projects/``:id``/tasks/``:id``/updates/
  - *GET*: return consolidated updates of a task
/projects/``:id``/tasks/``:id``/comments/
  - *GET*: return the comments (only) of a task
  - *POST*: create a new comment
/projects/``:id``/tasks/``:id``/comments/``:id``
  - *POST*: update a new comment (own or admin)
  - *DELETE*: delete comment (own or admin)
/projects/``:id``/tasks/``:id``/timesheet
  - *GET*: return the timesheet entry (only) of a task
  - *POST*: create a new timesheet entry
/projects/``:id``/tasks/``:id``/timesheet/``:id``
  - *POST*: update own timesheet entry not more than 2 days old
  - *DELETE*: delete own timesheet entry, not more than 2 days old. Admin can delete any entry
/projects/``:id``/tasks/``:id``/files/
  - *GET*: return all files of task
  - *POST*: upload a new file
/projects/``:id``/tasks/``:id``/files/``:id``
  - *GET*: return with file download url which it time sensitive
  - *DELETE*: delete the file
/users/``:id``/tasks/
  - *GET*: return current tasks of user

Authors and Contributors
------------------------

This module was built at `Openlabs <http://www.openlabs.co.in>`_. 

Professional Support
--------------------

This module is professionally supported by `Openlabs <http://www.openlabs.co.in>`_.
If you are looking for on-site teaching or consulting support, contact our
`sales <mailto:sales@openlabs.co.in>`_ and `support
<mailto:support@openlabs.co.in>`_ teams.
