## Environment Setup
* get mambaforge
* open a conda terminal
* clone this repo somewhere
```
cd path/to/widgetron
mamba env update --file=environment.yml --prefix=./.venv
mamba activate ./.venv
pip install -e .
widgetron -h
```

## Adding Functionality
It's just a bunch of jinja. Any parameters provided to the `[tools.widgetron]` section
of `pyproject.toml` or `setup.cfg` are made available to jinja on every template.
So, just try and use specific variable names and you should be good.
