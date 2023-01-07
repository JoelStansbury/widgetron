# widgetron
App bundler for ipywidgets

1. Builds and packages a simple electron interface to navigate to `localhost:8866`
2. Copies a designated notebook into a template python package
3. Makes a conda-package to hold the notebook
   - By default, this package only depends on `python`, `conda`, `voila`, and `ipywidgets`. So if your widget requires more stuff you'll need to explicitly add them.
   - Additional packages can be added to the `run` dependencies ([meta.yaml#L22](https://github.com/JoelStansbury/widgetron/blob/main/src/widgetron/templates/recipe/meta.yaml#L22)) via the `-deps` parameter. e.g. `widgetron -f my_notebook.ipynb -deps numpy my_conda_package scipy`.
   - These packages must be found either on `conda-forge` or in `local` (will add a `-c` arg soon)
4. Builds an installer

## Usage
```bash
mamba env create -f environment.yaml -p ./.venv
mamba activate ./.venv
pip install ./src
cd examples
widgetron -h
widgetron -f=my_notebook.ipynb -src=my_package
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
- Make a shortcut for the exe (maybe via post_install script)
- Add `-c` arg for conda channels
- Test on mac and linux
- Make `.ico` file to finalize the example
- Quit `voila` programatically
  - `voila` is launched on [main.js#L8](https://github.com/JoelStansbury/widgetron/blob/main/src/widgetron/templates/electron/main.js#L8). It seems to disconnect `voila` from the spawned process somehow, so it's proving difficult to kill.
