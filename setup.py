from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="buckaroo_sdk",
    version="1.0.0",
    author="Buckaroo",
    author_email="support@buckaroo.nl",
    description="A Python SDK for Buckaroo payment methods",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/buckaroo-it/BuckarooSDK_Python",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "httpx==0.28.0",
        "python-dotenv==1.0.1",
        "setuptools==75.8.0",
    ],
    extras_require={
        "dev": [
            "mypy==1.13.0",
            "pytest==8.3.3",
            "black==24.10.0",
            "types-setuptools==75.6.0.20241223"
        ],
    },
)
