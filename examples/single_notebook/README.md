```
.
└───nb
    |   my_notebook.ipynb
    └───my_package
            my_module.py
            __init__.py
```
A project structure like this should use something like
```bash
conda env create -f environment.yml -p .envs/dev
widgetron .
```