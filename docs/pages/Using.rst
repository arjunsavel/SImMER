Quickstart
============

PHARO reduction
---------------
We'll walk through an example of using this code on the PHARO data contained within the test suite.

First, run the below line to instantiate the code:

.. code-block:: bash

    import insts as i
    import drivers

    inst = i.PHARO() 

This instantiates :code:`inst` as an :code:`instrument` object prepared to reduced PHARO data.

Next, you'll want to set up your config file path, raw data directory, and reduced data directory. :code:`path_to_package` should be a path ending in :code:`shane-reduction/`.

.. code-block:: bash

    path_to_package = ... # edit this line!

    config_file = path_to_package +  'config.csv'
    raw_dir = path_to_package + src/simmer/tests/PHARO_integration

    reddir = ... # edit this line!

Finally, run 

.. code-block:: bash

    drivers.all_driver(inst, config_file, raw_dir, reddir)

Progress bars should give estimates as to how long each step will take along the way.

Now, check your :code:`reddir` folder — you should find your reduced data! Each :code:`sh**.fits` file is a shifted (centered) frame. The image that you'll likely want to use for your science is :code:`final_im.fits`.

ShARCS reduction
-----------------
Similarly to the PHARO method, we begin by instantiating the code — but this time, with a different instrument

.. code-block:: bash

    import insts as i
    import drivers

    inst = i.ShARCS() 

This instantiates :code:`inst` as an :code:`instrument` object prepared to reduced ShARCS data.

Next, you'll want to set up your config file path, raw data directory, and reduced data directory. :code:`path_to_package` should be a path ending in :code:`shane-reduction/`.

.. code-block:: bash

    path_to_package = ... # edit this line!

    config_file = path_to_package +  'config.csv'
    raw_dir = path_to_package + src/simmer/tests/ShARCS_integration

    reddir = ... # edit this line!

Finally, run 

.. code-block:: bash

    drivers.all_driver(inst, config_file, raw_dir, reddir)



