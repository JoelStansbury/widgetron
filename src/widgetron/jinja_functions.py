from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader

WIDGETRON_SRC = Path(__file__).parent
TEMPLATES = WIDGETRON_SRC / "templates"
COMMON_ARGS = dict(
    autoescape=False,
    loader=FileSystemLoader(str(TEMPLATES)),
    trim_blocks=False,
)
TEMPLATE_ENVIRONMENT = Environment(**COMMON_ARGS)
RECIPE_ENVIRONMENT = Environment(
    **COMMON_ARGS,
    block_start_string="<%",
    block_end_string="%>",
    variable_start_string="<<",
    variable_end_string=">>",
)


def _render(template_path, **kwargs):
    """
    template_path: path to template (relative to templates folder)
    """
    env = TEMPLATE_ENVIRONMENT
    if "recipe.yaml" in Path(template_path).name:
        env = RECIPE_ENVIRONMENT
    template = env.get_template(str(template_path))
    return template.render(**kwargs)


def render_templates(**kwargs):
    """
    Renders all templates, replacing all instances of {{kw}} with the value
    provided in kwargs.
    """
    outdir = kwargs["temp_files"]
    outdir.mkdir(exist_ok=True)

    for f in TEMPLATES.rglob("*_template"):
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
