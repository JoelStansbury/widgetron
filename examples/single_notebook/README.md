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
widgetron my_notebook.ipynb -n "Single-Notebook Example" -src my_package -icon icon.ico -deps numpy matplotlib ipywidgets -c conda-forge
```

## Takeaways
- `-src` may be either a single python script or a package as shown here
- `-icon` must be the correct type for the platform being built for (`.ico` for windows, `.png` or `.svg` for linux, and `.icns` for osx)
- `-deps` are expected to be found on `conda-forge`. If this is not the case, you will need to specify additional `--channels`.
  - e.g. `widgetron my_notebook -deps pytorch -c pytorch