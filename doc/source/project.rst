.. _nereid_project:
   
Welcome To Nereid Project
=========================

This documentation is divided into different parts. We recommend that you get 
started with :ref:`installation` and then head over to the :ref:`quickstart`.

**Nereid Project** is an open-source collaborative development platform offered
by Team Openlabs. It is mainly used for managing project processes. While it
could be used for managing any kind of project, it is primarily used at
Openlabs to manage software projects. It is designed to help organise projects
& tasks. The aim is to connect everything together on a single interface,
avoiding unnecessary time consumption, and track project's progress, task's
status, shared files, time spent on individual tasks.

* Break project into multiple tasks, assign to project teammates to collaborate
* Gantt chart provides deep insights about progress
* Collaborative dashboard ties everything together
* Upload files from personal desktop, or internet link
* Organize efforts-Easily create, assign, and comment on tasks, so user always
  know what's getting done and who's doing it.
* Puts tasks together, so user can go to one place for all the history of the
  work.
* notifications via email make it effortless to stay on top of the details that
  matter to user.

and much more...

Overview
--------

The goal of nereid project is to provide a friendly web based user interface to 
stakeholders outside the company to the powerful project management module of 
Tryton.

* Separate user accounts for users outside the company (like customers) without 
  giving access to Tryton.

* Simplify the project management tasks to encourage participation from users
  who may not be tech savvy.

Nereid User
-----------

Nereid introduces a model of user management different from the default user 
management schema (res.user) of Tryton. Nereid project also makes use of the 
concept to provide logins to participants of the project. 
Internal employees of the company should in addition have their user accounts 
linked to their employee records so that timesheet entries can be marked by 
users who are also employees.

In addition, nereid project also introduces the idea of project administrators. 
Project administrators are created by adding nereid users to the project admins
section on the company module. This is due for deprecation and will be replaced
with the permissions system introduced in nereid. Nereid Users with the
nereid_project.admin permission will be automatically given admin rights to 
all projects.

.. note:: 
   Note that the permissions mentioned here are nereid.permissions and not the 
   regular Tryton access control user groups.
