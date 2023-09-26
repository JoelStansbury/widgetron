import pytest
import shutil
from uuid import uuid4
from pathlib import Path

HERE: Path = Path(__file__).parent
TEST_EXAMPLES: Path = HERE / "examples"

@pytest.fixture
def multiple_notebooks_example():
    dirname: Path = HERE / str(uuid4())
    shutil.copytree(
        src=str(TEST_EXAMPLES / "multiple_notebooks"),
        dst=str(dirname),
    )
    yield dirname
    shutil.rmtree(dirname, ignore_errors=True)


@pytest.fixture
def minesweeper():
    dirname: Path = HERE / str(uuid4())
    shutil.copytree(
        src=str(TEST_EXAMPLES / "minesweeper"),
        dst=str(dirname),
    )
    yield dirname
    shutil.rmtree(dirname, ignore_errors=True)