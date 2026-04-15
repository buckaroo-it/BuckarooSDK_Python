import os
import re
from codecs import open
from setuptools import setup, find_packages


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

long_description = open(os.path.join(ROOT_DIR, "README.md"), encoding="utf-8").read()

with open(os.path.join(ROOT_DIR, "buckaroo", "_version.py"), encoding="utf-8") as f:
    version_match = re.search(r'^VERSION\s*=\s*["\']([^"\']+)["\']', f.read(), re.MULTILINE)
if not version_match:
    raise RuntimeError("Cannot find VERSION in buckaroo/_version.py")
version_contents = {"VERSION": version_match.group(1)}
    
setup(
    name="buckaroo-sdk-python",
    version=version_contents["VERSION"],
    description="Python bindings for the Buckaroo API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Buckaroo",
    author_email="wecare@buckaroo.nl",
    url="https://github.com/buckaroo-it/BuckarooSDK_Python",
    license="MIT",
    keywords="buckaroo api payments",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"buckaroo": ["data/ca-certificates.crt", "py.typed"]},
    zip_safe=False,
    install_requires=[
        'typing_extensions >= 4.5.0',
        'requests >= 2.20',
    ],
    python_requires=">=3.8",
    project_urls={
        "Bug Tracker": "https://github.com/buckaroo-it/BuckarooSDK_Python/issues",
        "Changes": "https://github.com/buckaroo-it/BuckarooSDK_Python//blob/master/CHANGELOG.md",
        "Documentation": "https://docs.buckaroo.io/",
        "Source Code": "https://github.com/buckaroo-it/BuckarooSDK_Python/",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    setup_requires=["wheel"],
)