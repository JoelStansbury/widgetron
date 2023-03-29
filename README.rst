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

   usage: widgetron [-h] [-o OUTDIR] [-nb NOTEBOOK] [-v VERSION]
                  [-env ENVIRONMENT_YAML]
                  [-deps DEPENDENCIES [DEPENDENCIES ...]]
                  [-c CHANNELS [CHANNELS ...]] [-src PYTHON_SOURCE_DIR]
                  [-sc SERVER_COMMAND [SERVER_COMMAND ...]] [-icon ICON]
                  [directory]

   Creates an app for displaying the output cells of an interactive notebook.

   positional arguments:
   directory             Directory to build in. This is also where the utility
                           will search for relevant config files (i.e.
                           `environment.yml`, `setup.cfg`, `pyproject.toml`)

   options:
   -h, --help            show this help message and exit
   -o OUTDIR, --outdir OUTDIR
                           Where to put the installer.
   -nb NOTEBOOK, --notebook NOTEBOOK
                           Path to notebook to convert. (must be .ipynb)
   -v VERSION, --version VERSION
                           Version number.
   -env ENVIRONMENT_YAML, --environment_yaml ENVIRONMENT_YAML
                           Path to environment.yml
   -deps DEPENDENCIES [DEPENDENCIES ...], --dependencies DEPENDENCIES [DEPENDENCIES ...]
                           List of conda-forge packages required to run the widget (pip packages are not
                           supported). If environment_yaml or explicit_lock are also provided, then those
                           are appended to the list of dependencies.
   -c CHANNELS [CHANNELS ...], --channels CHANNELS [CHANNELS ...]
                           List of conda channels required to find specified packages. Order is obeyed,
                           'local' is always checked first. Default=['conda-forge',]. If environment_yaml or
                           explicit_lock are also provided, then those are appended to the list of channels.
   -lock EXPLICIT_LOCK, --explicit_lock EXPLICIT_LOCK
                           Path to lock file generated via `conda-lock --kind=explicit`.
   -src PYTHON_SOURCE, --python_source PYTHON_SOURCE
                           This is a shortcut to avoid needing to build a conda package for your source
                           code. Widgetron is basically a big jinja template, if your notebook has `from
                           my_package import my_widget` then you would pass C:/path/to/my_package, and the
                           directory will by copied recursively into a package shell immediately next to the
                           notebook.
   -sc SERVER_COMMAND [SERVER_COMMAND ...], --server_command SERVER_COMMAND [SERVER_COMMAND ...]
                           How to launch JupyterLab. Default `["jupyter", "lab", "--no-browser"]`
   -icon ICON, --icon ICON
                           256 by 256 icon file (must be appropriate to OS) win: .ico osx: .icns linux: .png

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
