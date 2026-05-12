import os
from setuptools import setup, find_packages


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(ROOT_DIR, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

version_contents = {}
with open(os.path.join(ROOT_DIR, "buckaroo", "_version.py"), encoding="utf-8") as f:
    exec(f.read(), version_contents)

setup(
    name="buckaroo-sdk",
    version=version_contents["VERSION"],
    description="Python bindings for the Buckaroo API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Buckaroo",
    author_email="support@buckaroo.nl",
    url="https://github.com/buckaroo-it/BuckarooSDK_Python",
    license="MIT",
    keywords="buckaroo api payments",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"buckaroo": ["py.typed"]},
    zip_safe=False,
    install_requires=[
        "typing_extensions >= 4.5.0",
        "requests >= 2.20",
    ],
    python_requires=">=3.9",
    project_urls={
        "Homepage": "https://www.buckaroo.nl",
        "Bug Tracker": "https://github.com/buckaroo-it/BuckarooSDK_Python/issues",
        "Changes": "https://github.com/buckaroo-it/BuckarooSDK_Python/blob/master/CHANGELOG.md",
        "Documentation": "https://github.com/buckaroo-it/BuckarooSDK_Python#readme",
        "Source Code": "https://github.com/buckaroo-it/BuckarooSDK_Python/",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
