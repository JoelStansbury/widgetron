.. figure:: https://user-images.githubusercontent.com/48299585/213842033-c0c19779-84b9-4a07-83a0-9b75ef4b3971.JPG
   :alt: image
   :width: 500

This command line utility builds a standalone executable installer for a
single ipython notebook. It is intended for applications built with
ipywidgets.


Quickstart
----------

.. code:: bash

   conda install boa constructor nodejs -c conda-forge
   pip install widgetron
   widgetron -h

How it Works
~~~~~~~~~~~~

1. Builds and packages a minimal electron interface to navigate to
   ``localhost:8866`` and boot up the ``jupyter lab`` server
2. Copies a notebook (specified by ``-f``) into a template python
   package
3. Copies the entire contents of the built electron application into the
   template python package.
4. Optionally copies a source code directory (specified by ``-src``), if
   provided, into the template python package.

   -  The package specifies ``**`` for package_data so be sure to clean
      out any ``__pycache__`` folders and other garbage.
   -  Must be a valid python package (i.e. the folder must contain
      ``__init__.py``)

5. Makes a conda-package out of the python package template to hold the
   notebook, electron app, and source code if provided.
6. Builds an installer

   -  Conda dependencies are specified with the ``-deps`` parameter (see
      example).

Help
----

::

   usage: widgetron [-h] [-deps DEPENDENCIES [DEPENDENCIES ...]] [-c CHANNELS [CHANNELS ...]] [-n NAME] [-o OUTDIR] [-v VERSION]
                    [-src PYTHON_SOURCE_DIR] [-icon ICON]
                    file

   Creates an electron app for displaying the output cells of an interactive notebook.

   positional arguments:
     file                  Path to notebook to convert. (must be .ipynb)

   options:
   -h, --help            show this help message and exit
   -deps DEPENDENCIES [DEPENDENCIES ...], --dependencies DEPENDENCIES [DEPENDENCIES ...]
                           List of conda-forge packages required to run the widget (pip packages are not supported).
   -c CHANNELS [CHANNELS ...], --channels CHANNELS [CHANNELS ...]
                           List of conda channels required to find specified packages. Order is obeyed, 'local' is always
                           checked first. Default= ['conda-forge',]
   -n NAME, --name NAME  Name of the application (defaults to the notebook name).
   -o OUTDIR, --outdir OUTDIR
                           App version number.
   -v VERSION, --version VERSION
   -src PYTHON_SOURCE_DIR, --python_source_dir PYTHON_SOURCE_DIR
                           This is a shortcut to avoid needing to build a conda package for your source code. Widgetron
                           is basically a big jinja template, if your notebook has `from my_package import my_widget`
                           then you would pass C:/path/to/my_package, and the directory will by copied recursively into a
                           package shell immediately next to the notebook.
   -icon ICON, --icon ICON
                           Icon for app. Must be a .ico file

Example Usage
-------------

::

   git clone https://github.com/JoelStansbury/widgetron.git
   cd widgetron
   pip install ./src
   cd examples
   widgetron my_notebook.ipynb -src my_package -icon icon.ico -deps numpy matplotlib

Results
~~~~~~~

After the ``widgetron`` command the installer is placed in the current
working directory

.. figure:: https://user-images.githubusercontent.com/48299585/211173752-212a2d77-9238-412f-81f8-0f942f276749.png
   :alt: image


Running the installer

.. figure:: https://user-images.githubusercontent.com/48299585/211173763-fc7b54ad-c8cf-4386-94d8-cfc90cdb77d8.png
   :alt: image


Startmenu Shortcut

.. figure:: https://user-images.githubusercontent.com/48299585/211173745-9142808c-6303-4925-b1f2-d7db21430df1.png
   :alt: image


Window

.. figure:: https://user-images.githubusercontent.com/48299585/211173814-af05502c-2c41-4bd1-ad09-324a9eccef78.png
   :alt: image


Profit
