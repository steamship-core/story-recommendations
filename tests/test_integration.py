"""Unit tests for the package."""

import json
import logging
import random
import string
from pathlib import Path
from time import sleep
from typing import Optional

from steamship import Steamship, Task
from steamship.utils.url import Verb

from api import ImageGeneratorPackage

STEAMSHIP_JSON = Path(__file__).parent.parent / "steamship.json"
EXAMPLES = Path(__file__).parent.parent / "examples"



def package_name():
    """Return the package name recorded in steamship.json."""
    with open(STEAMSHIP_JSON, "r") as f:
        manifest = json.loads(f.read())
        return manifest.get("handle")


def random_name() -> str:
    """Return a random name suitable for a handle that has low likelihood of colliding with another.

    Output format matches test_[a-z0-9]+, which should be a valid handle.
    """
    letters = string.digits + string.ascii_letters
    return f"test_{''.join(random.choice(letters) for _ in range(10))}".lower()  # noqa: S311


def example_input(name: str) -> dict:
    """Return the JSON example file as a dict."""
    with open(EXAMPLES / name, "r") as f:
        return json.loads(f.read())


def mock_steamship_use(klass):
    def add_method(klass, method, method_name=None):
        setattr(klass, method_name or method.__name__, method)

    def handle_kwargs(kwargs: Optional[dict] = None):
        if kwargs is not None and "wait_on_tasks" in kwargs:
            if kwargs["wait_on_tasks"] is not None:
                for task in kwargs["wait_on_tasks"]:
                    # It might not be of type Task if the invocation was something we've monkeypatched.
                    if type(task) == Task:
                        task.wait()
            kwargs.pop("wait_on_tasks")
        return kwargs

    def invoke(self, path: str, verb: Verb = Verb.POST, **kwargs):
        # Note: the correct impl would inspect the fn lookup for the fn with the right verb.
        path = path.rstrip("/").lstrip("/")
        fn = getattr(self, path)
        new_kwargs = handle_kwargs(kwargs)
        print(f"Patched invocation of self.invoke('{path}', {kwargs})")
        res = fn(**new_kwargs)
        if hasattr(res, 'dict'):
            return getattr(res, 'dict')()
        # TODO: Handle if they returned a InvocationResponse object
        return res

    def invoke_later(self, path: str, verb: Verb = Verb.POST, **kwargs):
        # Note: the correct impl would inspect the fn lookup for the fn with the right verb.
        path = path.rstrip("/").lstrip("/")
        fn = getattr(self, path)
        new_kwargs = handle_kwargs(kwargs)
        invoke_later_args = new_kwargs.get("arguments", {}) # Specific to invoke_later
        print(f"Patched invocation of self.invoke_later('{path}', {kwargs})")
        return fn(**invoke_later_args)

    client = Steamship()
    add_method(klass, invoke)
    add_method(klass, invoke_later)
    obj = klass(client=client)

    return obj


def test_generate():

    pkg = mock_steamship_use(ImageGeneratorPackage)

    img_data = pkg.invoke(
        'generate',
        topic="A duck",
        mood="light",
        style="magazine",
        background="beach"
    )

