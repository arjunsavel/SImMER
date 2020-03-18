Quickstart
============

PHARO reduction
---------------
We'll walk through an example of using this code on the PHARO data contained within the test suite. The downloaded files will take up a few (~2) gigabytes of space, and they'll be placed in a folder in your current directory.


First, run the below line from the :code:`Python` interpreter or a Jupiter notebook cell to instantiate the code and download the data:

.. code-block:: bash

    import insts as i
    import drivers
    from tests.tests_1 import download_folder


    inst = i.PHARO() 
    download_folder('PHARO_integration')

This instantiates :code:`inst` as an :code:`instrument` object prepared to reduced PHARO data.

Next, you'll want to set up your config file path, raw data directory, and reduced data directory. :code:`path_to_package` should be a path ending in :code:`SImMER/`. 

.. code-block:: bash

    path_to_package = ... # edit this line!

    config_file = path_to_package +  'config.csv'
    raw_dir = 'PHARO_integration/'

    reddir = ... # edit this line!

Finally, run 

.. code-block:: bash

    drivers.all_driver(inst, config_file, raw_dir, reddir)

Progress bars should give estimates as to how long each step will take along the way.

Now, check your :code:`reddir` folder — you should find your reduced data! Feel free to delete the raw data folder afterward.

Each :code:`sh**.fits` file is a shifted (centered) frame. The image that you'll likely want to use for your science is :code:`final_im.fits`.

ShARCS reduction
-----------------
Similarly to the PHARO method, we begin by instantiating the code — but this time, with a different instrument and different data. The downloaded files will take up about a gigabyte of space, and they'll be placed in a folder in your current directory.

.. code-block:: bash

    import insts as i
    import drivers
    from tests.tests_1 import download_folder

    inst = i.ShARCS()
    download_folder('shane_quickstart')

This instantiates :code:`inst` as an :code:`instrument` object prepared to reduced ShARCS data.


Next, you'll want to set up your config file path, raw data directory, and reduced data directory. :code:`path_to_package` should be a path ending in :code:`SImMER/`.

.. code-block:: bash

    path_to_package = ... # edit this line!

    config_file = path_to_package +  'config_shane.csv'
    raw_dir = 'shane_quickstart/'

    reddir = ... # edit this line!

Finally, run 

.. code-block:: bash

    drivers.all_driver(inst, config_file, raw_dir, reddir)

Progress bars should give estimates as to how long each step will take along the way.

Now, check your :code:`reddir` folder — you should find your reduced data! Feel free to delete the raw data folder afterward.

Each :code:`sh**.fits` file is a shifted (centered) frame. The image that you'll likely want to use for your science is :code:`final_im.fits`. 

