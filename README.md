# widgetron
App bundler for ipython notebooks.
This command line utility builds a standalone executable installer for a single ipython notebook. It is intended for applications build with ipywidgets.
At the moment, it only works on Windows, but there are plans to address cross-platform support.

1. Builds and packages a minimal electron interface to navigate to `localhost:8866` and boot up the `voila` server
2. Copies a notebook (specified by `-f`) into a template python package
3. Copies the entire contents of the built electron application into the template python package.
4. Optionally copies a source code directory (specified by `-src`), if provided, into the template python package.
   - The package specifies `**` for package_data so be sure to clean out any `__pycache__` folders and other garbage.
   - Must be a valid python package (i.e. the folder must contain `__init__.py`)
4. Makes a conda-package out of the python package template to hold the notebook, electron app, and source code if provided.
5. Builds an installer
   - Conda dependencies are specified with the `-deps` parameter (see example).

## Installation
```bash
mamba install boa constructor nsis nodejs -c conda-forge
pip install widgetron
```

## Example Usage
```
git clone https://github.com/JoelStansbury/widgetron.git
cd widgetron/examples
widgetron -f my_notebook.ipynb -src my_package --icon icon.ico -deps numpy matplotlib
```

## Help
```bash
widgetron -h
```
```
usage: widgetron [-h] -f FILE [-deps DEPENDENCIES [DEPENDENCIES ...]] [-p PORT] [-n NAME] [-o OUTDIR] [-v VERSION]
                 [-env CONDA_PREFIX] [-src PYTHON_SOURCE_DIR] [--icon ICON]

Creates an electron app for displaying the output cells of an interactive notebook.

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to notebook to convert. (must be .ipynb)
  -deps DEPENDENCIES [DEPENDENCIES ...], --dependencies DEPENDENCIES [DEPENDENCIES ...]
                        List of conda-forge packages required to run the widget (pip packages are not supported).
  -c CHANNELS [CHANNELS ...], --channels CHANNELS [CHANNELS ...]
                        List of conda channels required to find specified packages. Order is obeyed. Any specified
                        channels are followed by local and conda-forge (so don't add either of those)
  -p PORT, --port PORT  4-digit port number on which the notebook will be hosted.
  -n NAME, --name NAME  Name of the application (defaults to the notebook name).
  -o OUTDIR, --outdir OUTDIR
                        Output directory.
  -v VERSION, --version VERSION
                        App version number.
  -src PYTHON_SOURCE_DIR, --python_source_dir PYTHON_SOURCE_DIR
                        Use with caution. This is a shortcut to avoid needing to build a conda package for your source
                        code. Widgetron is basically a big jinja template, if your notebook has `from my_package
                        import my_widget` then you would pass C:/path/to/my_package, and the directory will by copied
                        recursively into a package shell immediately next to the notebook.
  --icon ICON           Icon for app.

example usage: widgetron -f=my_notebook.ipynb
```

## TODO
- Test on mac and linux
- Hide menu bar. It does nothing
- Taskbar icon is not correct (uses default electron icon)
- Quit `voila` programatically
  - `voila` is launched on [main.js#L8](https://github.com/JoelStansbury/widgetron/blob/main/src/widgetron/templates/electron/main.js#L8). It seems to disconnect `voila` from the spawned process somehow, so it's proving difficult to kill.
- Clean up metadata propagation.
- Allow multiple `-src` directories
- Investigate the possibility to bundle multiple notebooks (I think I saw somewhere that `voila` can host more than one)
- Upload to pypi and conda-forge
- Better page loading
  - I only saw this once during development, but `index.html` redirected to `localhost:8866` before `voila` finished booting up and the app was unresponsive.


## Results
After the `widgetron` command the installer is placed in the current working directory

![image](https://user-images.githubusercontent.com/48299585/211173752-212a2d77-9238-412f-81f8-0f942f276749.png)

Running the installer

![image](https://user-images.githubusercontent.com/48299585/211173763-fc7b54ad-c8cf-4386-94d8-cfc90cdb77d8.png)

Startmenu Shortcut

![image](https://user-images.githubusercontent.com/48299585/211173745-9142808c-6303-4925-b1f2-d7db21430df1.png)

Window

![image](https://user-images.githubusercontent.com/48299585/211173814-af05502c-2c41-4bd1-ad09-324a9eccef78.png)

Profit
