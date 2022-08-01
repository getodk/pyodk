import os
import os.path
import shutil


def clean():
    """
    Delete directories which are created during sdist / wheel build process.

    Cross-platform method as an alternative to juggling between:
    Linux/mac: rm -rf [dirs]
    Windows:   rm -Recurse -Force [dirs]
    """
    proj = os.path.dirname(os.path.dirname(__file__))
    dirs = ["build", "dist", "pyodk.egg-info"]
    for d in dirs:
        path = os.path.join(proj, d)
        if os.path.exists(path):
            print("Removing:", path)
            shutil.rmtree(path)


if __name__ == "__main__":
    clean()
