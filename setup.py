# Inspired by:
# https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/

import codecs
import os
import re

from setuptools import find_packages, setup

###################################################################

NAME = "simmer"
PACKAGES = find_packages(where="src")
META_PATH = os.path.join("src", "simmer", "__init__.py")
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Natural Language :: English",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Scientific/Engineering :: Astronomy",
]
INSTALL_REQUIRES = [
    "numpy",
    "tqdm",
    "pandas==1.0",
    "astropy <4.1, >=3.1.2",
    "openpyxl>=2.5.12",
    "scipy <1.5.3, >=1.1.0",
    "matplotlib <3.1.1,>=3.0.1",
    "Scikit-image>=0.16.2",
    "pillow>=6.2.0",
    "pyyaml>=5.3.1",
    "cerberus>=1.3.2",
    "nbsphinx==0.5.1",
    "nbconvert==5.6.1",
    "pygments>=2.4.2",
    "xlrd>=1.2.0",
]

###################################################################

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=find_meta("uri"),
        version=find_meta("version"),
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
        package_data={"": ["README.md", "LICENSE"]},
        long_description=read("README.md"),
        long_description_content_type="text/markdown",
        packages=PACKAGES,
        package_dir={"": "src"},
        zip_safe=False,
        python_requires=">3.6.0",
        classifiers=CLASSIFIERS,
        include_package_data=True,
        install_requires=INSTALL_REQUIRES,
        options={"bdist_wheel": {"universal": "1"}},
    )
