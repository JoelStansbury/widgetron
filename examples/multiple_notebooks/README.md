```
.
│   my icon.ico
│
└───notebooks
    │   another one.ipynb
    │   my_notebook.ipynb
    │
    └───my_package
            my_module.py
            __init__.py
```


A project structure like this should use something like
```bash
widgetron notebooks -n "Multi-Notebook Example" -icon "my icon.ico" -deps numpy matplotlib ipywidgets -c conda-forge
```

> `-src` is disabled if `-f` is a directory. 
> If you have src files and it is not possible to have them be relatively imported by the notebooks,
> then you'll need to create a conda package for them. It is sufficient
> to just do `conda mambabuild YOUR-RECIPE` and add the package name to the
> `--dependencies` parameter. If you use the `--output-folder` arg, then you would also
> need to provide the path to that local channel in the `--channels` parameter.

## Takeaways
- You cannot specify a notebook directory (`-f`) AND python source code (`-src`)
- You may place source code directly in the directory
- The source directory will be visible in the application
- The user may choose any notebook found within the `-f` directory, but there is currently no way to go back and run another. (For that, they'll need to restart the application)
