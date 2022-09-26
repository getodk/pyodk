from setuptools import find_packages, setup

from pyodk import __version__

setup(
    name="pyodk",
    version=__version__,
    author="github.com/getodk",
    author_email="support@getodk.org",
    packages=find_packages(exclude=["tests", "tests.*"]),
    url="https://pypi.python.org/pypi/pyodk/",
    description="The official Python library for ODK 🐍",
    long_description=open("README.md", "r").read(),
    long_description_content_type='text/markdown',
    license="Apache License, Version 2.0",
    python_requires=">=3.8",
    install_requires=(
        "requests==2.28.1",
        "toml==0.10.2",
        "pydantic==1.10.1",
    ),
)
