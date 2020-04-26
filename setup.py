from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="PyDataSocket",
    version="0.0.1",
    author="Peter Somers",
    author_email="psvd3@mst.edu",
    description="A Python module for sending data across TCP sockets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/psomers3/PyDataSocket.git",
    packages=['DataSocket'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3',
)
