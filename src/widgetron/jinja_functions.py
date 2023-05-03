from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader

WIDGETRON_SRC = Path(__file__).parent
TEMPLATES = WIDGETRON_SRC / "templates"
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(str(TEMPLATES)),
    trim_blocks=False,
)


def _render(template_path, **kwargs):
    """
    template_path: path to template (relative to templates folder)
    """
    template = TEMPLATE_ENVIRONMENT.get_template(str(template_path))
    return template.render(**kwargs)


def render_templates(**kwargs):
    """
    Renders all templates, replacing all instances of {{kw}} with the value
    provided in kwargs.
    """
    outdir = kwargs["temp_files"]
    outdir.mkdir(exist_ok=True)

    for f in TEMPLATES.rglob("*.*"):
        rel = f.relative_to(TEMPLATES)
        intermediate_folders = rel.parts[:-1]

        # Create sub-directories in output folder
        for i in range(len(intermediate_folders)):
            subdir = "/".join(intermediate_folders[: i + 1])
            (outdir / subdir).mkdir(exist_ok=True)

        p = outdir / rel

        if p.suffix.endswith("_template"):
            p = p.with_suffix(p.suffix.replace("_template", ""))
            with open(p, "w") as f:
                f.write(_render("/".join(rel.parts), **kwargs))
        else:
            shutil.copyfile(TEMPLATES / "/".join(rel.parts), str(p))
