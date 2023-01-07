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
conda env create -f environment.yaml -p ./.venv
conda activate ./.venv
pip install ./src
cd examples
widgetron -f=my_notebook.ipynb -src=my_package
```

## TODO
- Make a shortcut for the exe (maybe via post_install script)
- Add `-c` arg for conda channels
- Test on mac and linux
- Make `.ico` file to finalize the example
- Quit `voila` programatically
  - `voila` is launched on [main.js#L8](https://github.com/JoelStansbury/widgetron/blob/main/src/widgetron/templates/electron/main.js#L8). It seems to disconnect `voila` from the spawned process somehow, so it's proving difficult to kill.
