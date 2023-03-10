```
.
│   icon.ico
│   my_notebook.ipynb
│
└───my_package
        my_module.py
        __init__.py
```
A project structure like this should use something like
```bash
widgetron --explicit_lock="conda-win-64.lock"
```

This module demonstrates two important concepts.
1. use of conda lock files

    The `--explicit-lock` argument is intended to be purely a cli argument. It does not
    make much sense being defined in a config file unless you only intend to build for
    a single platform. The file passed into this argument is expected to contain a list
    of urls to conda packages after a line containing `@EXPLICIT`.

    Providing this lock file significantly reduces the time required to build the installer
    as it makes solving the final environment much easier.


2. inclusion of raw python source code

    This is pretty jank, so I don't recommend using it for production builds. But for 
    just testing stuff out, the folder/file passed into the `python_source` argument
    will be copied and placed immediately next to the notebook so it can be imported
    relatively.