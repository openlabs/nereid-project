.. _tutorial:
   
Nereid Project Tutorial
=======================

This tutorial gives an overview into how nereid project is organized and how it 
works with the Tryton project module. Familiarity with the tryton project
module is not assumed, but could make the project easier to understand. Follow
:ref:`quickstart` before starting this tutorial.

Creating Your First Project
----------------------------

For getting started you need to have a project and team members working on
it. So let's get started with creating a project.

When logged in as a project admin, see :ref:`admin`, the admin can create a
new project, invite new or existing users to the project and change the
setting related to the project. Now when project is created, all the feature
regarding that project is visible.

* Click the New Project button (found at the top right of every Project
  Management Page)

* A modal window will then slide into view, where you will find fields for
  entering the title of the project. Once you are done, click Save.

* You will now be taken to the Project overview screen, you have just created
  your first project!
  
See the screen-shot shown below: 

.. _project management screen:

.. image:: images/project-page.png

You can invite your team members to collaborate and work together on a
project. The invites can be your team member and also your client for
whom you have created this project.

To invite a use go to **People and Permissions** and enter the email address
of the person you wanted to invite. An invitation email will be sent to
the user. The user can now check the project, create tasks, mark time etc.


.. note::
    Only the project admin <:ref:`admin`> can create the projects on Project
    Management System.

Creating project on Tryton client
---------------------------------

Alternatively projects could be created from your preferred Tryton client,
go to Projects from the left panel and follow the steps below:
 
1. Click the Create New button (found at the top left of every form view in
   Tryton)

2. Where you will find fields for entering the title of the project, the type
   (whether project or a task), Company, participants or assignee (if any),
   State of the project(opened or done).

3. Once you are done, click on Save button found at top left of the form view,
   next to New button.

.. image:: images/create-project.png

If the project admin adds the project, or performs any changes through Tryton
client, it also gets updated to web-interface, and vice-versa.

Adding Participants to Project via Tryton Client
------------------------------------------------

Through project permissions you can control your employees access. The
participants to the project can only be added by the project admin through
Tryton client as shown below in the screenshot, participants are then allowed
to do list of following things - can view project, contributes to the project,
create tasks, updates the progress made so far, change the state of the task,
assign the task to other participant of that project, mark their time, etc.

This below figure shows how to add the project participants on Tryton client:

.. image:: images/project-participant.png


Changing State:
```````````````

The project can be in open or done state. Status of the project can be
changed by a project admin. To close a project simply from the admin page.

.. note:: State can be changed only by project admin

.. _invitation:

The Project Management Screen
-----------------------------

.. figure:: images/dashboard.png

The screenshot shown above is the main dashboard of the system. You can
open a project and you will start working on it. You can see there are
some side menus available on the left hand side of the screen.
You can go to the *Task* menu and start creating tickets for the project.

So at the very top we have the project title, next we have the following
features:

* **Dashboard:** Where a list of of all projects are shown depending upon the
  permissions granted to that nereid user. For more information, see
  `dashboard`_.
  
* **Tasks:** Every single project can have multiple tasks assigned to it.
  Participant of the project can create tasks depending upon the requirements
  to achieve the goal of the project as soon as possible. The tasks are
  displayed according to the states. This view is called Kanban View.
  See `tasks`_.

* **Time Sheets:** The timesheet module allows to track the time spent by
  employees on various tasks. This module also comes with several reports that
  show the time spent by employees. For more refer `timesheet`_.

* **Planning:** This uses the feature of gantt charts and it allows all the
  team members to check the planned task according to its estimated time. The
  Nereid Project has a wonderful interface that is completely intuitive.
  Refer `planning`_.

* **Files:** Attaching a file is very easy in the Nereid Project. You can
  attach as many as files you want. You can also see the preview of the
  images on the task itself. Learn more about it in `files`_.

* **People and Permissions:** The project admin can invite and remove users
  from here. See `invitation`_.

.. _tag:

* **Tags :** Creating a tag is only possible by admin. The admin can select a
  colour for tags and create tags. User can add tags along with the task.
  You can click the tags from the task view and see all the tasks tagged with
  it. For example, tag several tasks as *Priority* now you can just click the
  tag from the Kanban view and you can see all the task under that tag.
  
* **Estimated Effort** : You can also estimate a task. You just need to
  put the time needed to do one task. Learn more about it `estimated effort`_.


People and Permission
----------------------

Nereid project makes it very easy collaborate and work together on a
project. You can invite as many as user you want to your project. Only the
project admin can send the invitations. To invite a user just go to the
people and permission tab on the project view and add the email address of
the user you wanted to invite. That user can accept the invitation and
start collaborating to the project. 

This user can be a developer, designer, customer/client, vendor, etc.
Everybody can work together, and create tickets and assign it to each other.
The nereid project makes it very easy to get updated about the current
project. Where people from different zone can collaborate together. 

.. image:: images/people-n-permissions.png


.. _tasks:

Creating Task
--------------

You can click the **New Task** button on the top right section and create a
task. You can assign the task to another user of the same project, out the
start date and end date of the task, put estimation on the task and save
the task.

Once the task is created, it automatically goes to the backlog state. You can
update the task and keep assigning it to other members. Task is having
following features:

* You can update the task and assign it to another project member.
* You can also notify another member on the task by clicking the notify button
  along with the comment box.
* You can attach files on the task. Attaching files can be done by
  clicking the attach button next to *Files*. You can also directly drag
  and drop the file into the comment section.
* You can put the time you are taking to work on the task.
* You can change the state of the task from Backlog to, planning, in progress
  and Done.
* You can also watch someones task, by clicking the watch icon next to the
  task heading.
* All the members of the project will get email notification on their for
  every activity happening on the tasks they are watching or participating.

.. image:: images/create-task.png


.. note::
   Any nereid user having access to the project can create task, update the
   task, putt comments, upload files into it, and assign it to other
   nereid user of that project. See `update`_.

.. _reST primer:

Basic RST primer
----------------

This section is a brief introduction to reStructuredText (reST) concepts and
syntax, reST was designed to be a simple, unobtrusive markup language. For more
refer `RST primer <http://sphinx-doc.org/rest.html>`_

Lists
`````
Just place an asterisk at the start of a paragraph and indent properly. The
same goes for numbered lists; they can also be autonumbered using a ``#``
sign::
  
  * This is a bulleted list.
  * It has two items, the second
  item uses two lines.

   1. This is a numbered list.
   2. It has two items too.

   #. This is a numbered list.
   #. It has two items too.

Paragraph
`````````
As in Python, indentation is significant in reST, so all lines of the same
paragraph must be left-aligned to the same level of indentation.

Inline markup
`````````````
The standard reST inline markup is quite simple: use

* one asterisk: ``*text*`` for emphasis (italics),
* two asterisks: ``**text**`` for strong emphasis (boldface), and
* backquotes: ````text```` for code samples.

Code Highlighting
``````````````````
The highlighting language can be changed using the ``highlight`` directive, by
default, this is ``'python'`` as the majority of files will have to highlight
Python snippets used as follows::

     .. highlight:: c

An example in python code highlighting::

    .. code-block:: python

       def some_function():
           interesting = False
           print 'This is '
           print 'code highlighting'
           print '...'

.. _update:

Updating task
--------------

Task updates can be formatted using `reST primer`_ syntax for
making comments or updates looks clear. For more `reST(restructured Text)
<http://docutils.sourceforge.net/docs/ref/rst/directives.html>`_

Updates can be written to clarify progress made so far for the task, for
changing the state of the task, for marking time i.e., the time spent by the
employee on that task etc. While marking time user can also update the `state`_


.. image:: images/task.png


.. _timesheet:

Marking Time
`````````````

Nereid Project enables the team to record their time directly on their tasks on
every update. Each time the employee comments on a task, the time entered is
updated along with it. 

For marking time, see below: 

.. tip::
   User will need to understand how much time they are devoting to each task
   and mark time in hours. For marking time in minutes, convert those minutes
   to hours, like, for entering 6 minutes - mark '.1', for 30 minutes - mark
   '.5' and so on.

.. image:: images/time.png

View my-tasks
-------------

Project participants can see their task list, and these lists easily help user
to keep track of every assigned tasks on a project, quickly tells the `state`_,
and with `tag`_ (if associated to it)!

.. admonition:: And, by the way...

   Drag and Drop- To change the state of the task, just drag and drop task from
   one state to the necessary state. 

.. image:: images/my-tasks.png


View all tasks
```````````````
The participants can view all the tasks on a particular project. All the tasks
is listed according to Kanban View. So it is easy to check all the tasks
according to their states. Click Tasks from the side menu and see all the
tasks according to their states. You can also search for a particular task.

Features:

* Striped multi-colour tasks in Nereid Project - tasks with different colors
  signifies different `state`_
* You can instantly search for a task through task id or name.
* The "All Tasks" tab shows all the open and closed tasks. So the history of
  the project is also maintained.

To see All Tasks, Open Tasks, Done Tasks just click on the ``Tasks``
Button shown on the left, for reference see below:

.. image:: images/tasks-list.png


.. _state:

State of Task
-------------

.. image:: images/backlog.png
.. image:: images/planning1.png
.. image:: images/progress.png
.. image:: images/review.png
.. image:: images/done.png


Ideally all the user should keep the task updated to their respective states.
It will increase the transparency amongst the team members and the customer
involved in the project. All the states are explained below:

* **Backlog:** When you create a new task, by default it goes to the backlog
  state. You can either drag and drop the task to another state or update the
  state through the task view.
* **Planning:** If a task has been planned and the user know well, what needs
  to be done on that task, then it is kept on the planning state.
* **In Progress:** Once the user starts developing the task, he/she can
  drag and drop the task to "In Progress" state.
* **Review:** Now once the user is done with the task he/she can assign the 
  task to the assignee for review. The review state can go through several
  iteration before it get accepted by the assignee.
* **Done:** If requirements meets the scope of the task, then the task can
  be marked as Done.

In their simplest, the tasks are categorized into the work stages:

* from Backlog --> Planning

* from Planning --> In Progress

* from In Progress --> Review/ QA
    
* from Review/QA --> Done

Notify another participant
```````````````````````````

The participants can notify each other on their respective tasks. While
updating a task just click on ``Notify People`` button to add or remove
participants from the task. Now whenever this task will be updated, all the
participants will get notified through e-mail. See below, from where to
add-remove participants for the current task:

.. image:: images/notify.png


E-mail Notification
-------------------

An integral feature of the Nereid Project is email notification. All the
project participant receives an automated email notification from system.

.. estimated effort::

Estimated Effort
`````````````````

This feature allow a user to estimate the efforts that is going to be
used for a particular task. As there would be time consumption on
each task. This creates a more routine environment for the team members
allowing them to spend time on a planned way. So that every task has
achievable schedule objectives.
 
.. tip::
   To enter the estimated time afterwards creating the task. Click the
   ``Estimated Hours`` button on the left side of the web-interface, a modal
   window will slide into view, where you can enter the time.

.. image:: images/estimated-time.png


.. _files:
   
Attachment
----------

The user can attach files directly to tasks. There are two ways for attaching
file:

 * Drag and drop the file into the comment section,
 * Upload the file from your local machine or from dropbox.

.. image:: images/file-upload.png


To upload attachments to Nereid Project, follow these steps:

* Open up the task to attach a file, click Files button on the left side for
  attaching files or link, a modal window slide into view and from the
  drop-down menu, select type to attach i.e., to attach a link from the
  internet, or file to upload.

* Select the file/link you'd like to attach. Your file will appear in your task
  as shown in figure below.

.. image:: images/upload-file.png

The Files button shows all files that have been attached through individual
posted to the task. Files attached to the system are collected and displayed
here in Files section, along with filename, the description along with it, and
a link to the area where that file is being attached.The original file is
included along with a link to download the file.

.. image:: images/files-button.png

.. _dashboard:

Dashboard
``````````

The project dashboard gives a summary of active projects. Nereid Project's
Dashboard is a customized project information system containing list of
projects, for tracking team progress toward completing an iteration. 

.. tip:: 
   Only those projects are visible to user whose permission is provided by
   project admin.

.. image:: images/dashboard.png
   
Global Timesheet
-----------------

For Project Managers, and Owners - this Timesheet information 'completes the
picture' of project productivity and progress. Team members do not have access
to a global timesheet calendar which details every step within the project
timeline. It helps to delegate and track project tasks and manage the projects
effectively.

This timesheet and online project management application helps to track, or
monitor every hour that is spent on a project, by whom and how they did with
regards to staying within your expected target durations. 

.. image:: images/global-timesheet.png

.. tip::
   Project admin can filter the performance by employees also. See top-left
   side of this global timesheet page, there is a search box, enter the name of
   employee to checkout the performance, to track total hours spent by
   individual on that task. Use timesheet to efficiently record the
   “Hours Worked” (per Project, or Task). By using this, project admin can view
   the team's progress and determine whether the team is making sufficient
   progress.

.. image:: images/timesheet-lines.png

The timesheet line express the fact that one employee spend a part of his/her
time on a specific work at a given date. The list of timesheet lines of
employees associated to the project and its tasks. These timesheet lines are
used to analyse employee's productivity & job costs.

Weekly Analysis
````````````````

To gather data weekly on the actual time spent by employee. For time tracking
to monitor employees performance. The :ref:`admin` can analyse the progress of
the team of the project. You can filter it by employee's name also. 
Refer image:

.. image:: images/weekly-analysis.png

Task by employees
``````````````````

It show the task assigned to all your employees throughout the project
management system in Kanban view. It is also visible to the project admin.
:ref:`admin`

.. image:: images/tasks-employee.png

.. _planning:

Calendar 
`````````

The calendar is directly tied to the ongoing projects. The calendar show a
graphical calendar interface with all of the pertinent ongoing tasks. It is
able to filter by month, week or day. Access to calendars and the tasks held
within follow the same access, setup for projects. So that users will only see
the calendar items of the projects they are invited to. For project admin,
calendar provides a number of powerful filters. These filters let project admin
see performance of employees. This is a great feature for project admin to
track your progress on the graphical Gantt charts for their most highly valued
projects.

.. image:: images/calender.png


Here the logged in user can view the timesheet of his current project, and also
his performance for that project.

.. note:: 
   
   For admin, its easy-to-use, for tracking employee's marked time and
   performance. The row on timesheet lines shows their name, time they worked
   for which task. Shows total time, the employee worked per day.

Project Planning
-----------------

Creating a project plan is the first thing a user should do when taking any kind
of project by putting start and end time on its task. Project planning is a
feature used to reflect the duration of a task within a certain time period. It
is a known fact that a good project plan can make the difference between the
success or failure of a project.

Planning organize, schedule and ensure that tasks get done on time. On short it
can boost productivity. By being better organized and more focused on what have
to be done, and saves time.

This feature is used for projects, but only consist of a list of tasks. To
access it, go to ``Dashboard ‣ Projects Home ‣ New Project ‣ Planning`` ( Here
'New Project' is the name of the selected project ). User can select single
project at a time to see the planning. It shows the Gantt chart for tasks with
start and end time of task or just the duration.


.. image:: images/planning.png
