import os.path
import re

from setuptools import find_packages, setup

def get_long_description():
    return open(os.path.join(ROOT_DIR, "README.md"), encoding="utf-8").read()

def get_version():
    """Read the version from a file (buckaroo/api/version.py) in the repository.

    We can't import here since we might import from an installed version.
    """
    version_file = open(os.path.join(ROOT_DIR, "buckaroo", "api", "version.py"), encoding="utf=8")
    contents = version_file.read()
    match = re.search(r'VERSION = [\'"]([^\'"]+)', contents)
    if match:
        return match.group(1)
    else:
        raise RuntimeError("Can't determine package version")

setup(
    name="buckaroo-sdk",
    version=get_version(),
    license="BSD",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["buckaroo", "buckaroo.*"]),
    include_package_data=True,
    package_data={
        "buckaroo": ["py.typed"],
    },
    description="A Python SDK for Buckaroo payment methods",
    author="Buckaroo",
    author_email="support@buckaroo.nl",
    keywords=[
        "buckaroo",
        "payment",
        "service",
        "ideal",
        "creditcard"
    ],
    url="https://github.com/buckaroo-it/BuckarooSDK_Python",
    install_requires=[
        "requests",
        "urllib3",
        "requests_oauthlib",
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Office/Business :: Financial",
    ],
)
