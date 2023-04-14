<img src="https://user-images.githubusercontent.com/48299585/213842033-c0c19779-84b9-4a07-83a0-9b75ef4b3971.JPG" alt="drawing" width="500"/>

This command line utility builds a standalone executable installer for a
single ipython notebook. It is intended for applications built with
ipywidgets.

## Quickstart
```
conda install boa constructor nodejs jake -c conda-forge
pip install widgetron
widgetron -h
```

### How it Works

1. Builds and packages a minimal electron interface to navigate to
   `localhost:8866` and boot up the `jupyter lab` server
2. Copies a notebook (specified by `-f`) into a template python
   package
3. Copies the entire contents of the built electron application into the
   template python package.
4. Optionally copies a source code directory (specified by `-src`), if
   provided, into the template python package.

   -  The package specifies `**` for package_data so be sure to clean
      out any `__pycache__` folders and other garbage.
   -  Must be a valid python package (i.e. the folder must contain
      `__init__.py`)

5. Makes a conda-package out of the python package template to hold the
   notebook, electron app, and source code if provided.
6. Builds an installer

   -  Conda dependencies are specified with the `-deps` parameter (see
      example).

### Development Guide
Before you run `widgetron`
1. Create a conda environment yaml to define your dependencies

   - pip dependencies are not supported

2. If you want to create a Software Bill of Materials (SBOM), then you'll need to also lock this environment
   and provide the lockfile to the `explicit_lock` parameter.

3. Create a `pyproject.toml` or `setup.cfg` and follow the examples to see
   how these should be formatted.
4. If you have additional source code to include there are two options for how to do so

   - (Recommended) create a conda package (using `conda-build`) and add it to the `-deps` argument.
   - (Easy, and dangerous) Include the raw source files

      - If your `--notebook` argument is a single notebook, then point the `-src` parameter to the root of your python module.
      - If your `--notebook` argument is a directory, then your source code must be placed inside this directory and be relatively importable.
      - __Warning__: this includes __EVERYTHING__ so delete your `__pycache__`s and `.env`s etc.

4. Provide any metadata you want (see `widgetron -h` or `src/widgetron/args.yml` for options)

5. run `widgetron` in the same directory as the `toml` or `cfg` file

   - This will immediately render all of the templates so you can inspect them in a new `widgetron_temp_files` directory.
   - I recommend looking at `constructor/construct.yaml` and `server/widgetron_app/notebooks` especially.
   - If something is obviously wrong, stop widgetron and fix it.
   - Otherwise, wait for the installer to be created, then run it and make sure everything works.
   - If you get some import errors, then there's likely something missing from the environment.yml/lock
   - There's also a debug notebook that you can run to get some useful info about how jupyterlab is running.

### Example

After the `widgetron` command the installer is placed in the current working directory

![image](https://user-images.githubusercontent.com/48299585/211173752-212a2d77-9238-412f-81f8-0f942f276749.png)

Running the installer

![image](https://user-images.githubusercontent.com/48299585/211173763-fc7b54ad-c8cf-4386-94d8-cfc90cdb77d8.png)

Startmenu Shortcut

![image](https://user-images.githubusercontent.com/48299585/211173745-9142808c-6303-4925-b1f2-d7db21430df1.png)

Window

![image](https://user-images.githubusercontent.com/48299585/211173814-af05502c-2c41-4bd1-ad09-324a9eccef78.png)

Profit