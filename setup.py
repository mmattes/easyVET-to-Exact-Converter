#!/usr/bin/env python
try:
    from setuptools import setup
except:
    from ez_setup import use_setuptools
    use_setuptools()

extra = {}

setup(
    name="evconverter",
    packages=['evconverter'],
    zip_save=False,
    include_package_data=True,
    version="0.5.0",
    description="Converter for Bookkeeping data exported from a PMS",
    author="Markus Mattes",
    author_email="mmattes87@gmail.com",
    url="https://github.com/mmattes/easyVET-to-Exact-Converter",
    license="MIT license",
    keywords="easyVET exact bookkeeping",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Text Processing"
    ],
    long_description="""
    evconverter is a small script tools which helps to convert data created from a veterinary
    practice managment solution called easyVET to a bookkeeping solution called Exact. The
    exported data from the PMS (www.easyvet.eu, www.vetz.de) is existing in Text format with Tabs
    as seperator and will be converterd to the XML format of Exact (www.exact.nl)
    """,
    **extra
)
