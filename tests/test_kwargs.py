from subprocess import call

def test_multi_notebook(multiple_notebooks_example):
    rc = call(["widgetron", str(multiple_notebooks_example), "--template"])
    assert rc == 0
    root = multiple_notebooks_example
    tmp = root / "widgetron_temp_files"
    src = root / "notebooks"
    dst = tmp / "server/widgetron_app/notebooks/notebooks"
    src_files = [f.name for f in src.rglob("*.*")]
    dst_files = [f.name for f in dst.rglob("*.*")]
    assert set(src_files) == set(dst_files)