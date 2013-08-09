.. _installation:

Installation
=============

Install required OS packages
----------------------------

Some requirements to get installed, they might be in your package manager::

    sudo apt-get install python-dev
    sudo apt-get install python-pip

These are required for the Python package lxml::
    
    sudo apt-get install libxml2-dev
    sudo apt-get install libxslt-dev
    
Virtual Environment
--------------------

For getting this running on your local machine, the easy way to do that is 
setting up the `virtualenvwrapper`_ first. 

.. _virtualenvwrapper:

virtualenvwrapper
.................

`virtualenvwrappers`_ are isolated Python environments. This helps isolate your 
dependencies, especially when used with pip. virtualenvwrapper provides some 
convenient short-hand shell commands to make virtualenv nicer to use.

If you are on Mac OS X or Linux, the following command will work for you in 
creating a virtualenv 

.. code-block:: sh

   $ sudo pip install virtualenvwrapper

Set up virtualenvwrapper
^^^^^^^^^^^^^^^^^^^^^^^^

In your shell initialisation file 
(eg. ~/.bashrc), add two lines like this::

    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh

(Change the path to virtualenvwrapper.sh depending on where it was installed by 
pip.)

WORKON_HOME is a directory where virtualenvwrapper is going to collect the 
virtualenvs that you use it to create.

virtualenvwrapper provides the following commands::

    mkvirtualenv foo
    rmvirtualenv foo
    workon foo # activate the virtualenv called foo
    deactivate # whatever the currently active virtualenv is

Now ``Create`` a new virtualenv for project:

.. code-block:: sh

   $ mkvirtualenv myproject
   New python executable in myproject/bin/python
   Installing setuptools............done.
   Installing pip...............done.
   $ cd myproject
   $ cdvirtualenv


Now, whenever you want to work on a project, you only have to activate the
corresponding environment.  On OS X and Linux, do the following

.. code-block:: sh

    $ . venv/bin/activate

If you are a Ubuntu user, the following command is for you

.. code-block:: sh

    $ workon myproject
    (myproject)$

Either way, you should now be using your virtualenv (notice how the prompt of
your shell has changed to show the active environment).

How to install Nereid Project
-----------------------------

Nereid Project(a Project management system), has been implemented as a Web 
application to be accessed using a web browser.

To experience this you should have installed ``tryton client``. Following
commands is to be followed for installing Nereid Project's desktop client.

Nereid project can be installed like any other tryton module or python package
as it comes bundled with a setup.py script.
Alternatively the latest released version published to PYPI can be installed
using PIP.

.. code-block:: sh
   
   $ pip install trytond_nereid_project

A few seconds later and you are good to go.

So to start with, install following::

    pip install psycopg2
    pip install blinker

Both above packages should be installed by default but just in case to make
sure, it they were not, they get installed in your current working environment.

Now, nereid-project is installed, to run the web app, Project Management system,
refer :ref:`quickstart`.

.. _virtualenvwrappers: http://virtualenvwrapper.readthedocs.org/en/latest/
