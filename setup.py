from setuptools import find_packages, setup

from pyodk import __version__

setup(
    name="pyodk",
    version=__version__,
    author="github.com/getodk",
    author_email="support@getodk.org",
    packages=find_packages(exclude=["tests", "tests.*"]),
    url="http://pypi.python.org/pypi/pyodk/",
    description="The official Python library for ODK 🐍",
    long_description=open("README.md", "r").read(),
    license="Apache License, Version 2.0",
    python_requires=">=3.8",
)
