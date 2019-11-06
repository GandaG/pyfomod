import webbrowser
from pathlib import Path

import pytest
from invoke import task

ROOT_FOLDER = Path(__file__).resolve().parent


@task
def isort(c):
    c.run("isort -m 3 -tc -fgw 0 -up -w 88 -rc src/pyfomod tests tasks.py")


@task
def black(c):
    c.run("black src/pyfomod tests tasks.py")


@task
def flake(c):
    c.run(
        "flake8 --max-line-length=80 --select=C,E,F,W,B,B950 "
        "--ignore=B305,E203,E501,E731,W503 src/pyfomod tests tasks.py"
    )


@task(pre=[isort, black, flake])
def check(c):
    pass


@task
def test(c):
    pytest.main(["-rsx", "tests/"])


@task
def docs(c, open=False):
    docs_folder = ROOT_FOLDER / "docs"
    with c.cd(str(docs_folder)):
        c.run("make html")
        c.run("make linkcheck")
    if open:
        html_path = docs_folder / "_build" / "html" / "index.html"
        webbrowser.open(html_path)
