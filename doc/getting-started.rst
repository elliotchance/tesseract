Getting Started
===============

Installation
------------

Since tesseract is very alpha I have not uploaded releases yet to ``pip`` so the
easiest way get it is to clone out the repo and run off the stable ``master``
branch. You can view the :ref:`changelog`.

.. code-block:: bash

   git clone https://github.com/elliotchance/tesseract.git


Running the Server
------------------

You must have Redis running locally on the standard port. If not, run:

.. code-block:: bash

   redis-server &

Then start the tesseract server. It's not wise to run it in the background so
you can pay attention to errors and crashes during this wonderful time of
alpha.

.. code-block:: bash

   bin/tesseract

Remember that if you pull the latest changes for tesseract you will have to
restart the server for those changes to take effect. Simply ``CTRL+C`` and run
the command above again.
