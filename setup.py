from setuptools import setup


with open("README.md", "r") as fh:
    long_description = fh.read()

from distutils.dir_util import copy_tree, remove_tree
copy_tree('Matlab', 'DataSocket/Matlab')

setup(
    name="PyDataSocket",
    version="0.0.4",
    author="Peter Somers",
    author_email="psvd3@umsystem.edu",
    description="A Python module for sending data across TCP sockets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/psomers3/PyDataSocket.git",
    packages=['DataSocket'],
    package_data={'DataSocket': ['Matlab/TCPReceiveSocket.m', 'Matlab/TCPSendSocket.m']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux :: Windows :: OSX",
    ],
    python_requires='>=3',
    install_requires=['numpy',
                      'h5py']
)

remove_tree('DataSocket/Matlab')