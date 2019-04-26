#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests>=2.7.0',
    'pycountry>=18.5.26',
    'pycryptodome>=3.6.6',
]

setup_requirements = [
    # TODO(vilkasgroup): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='verifone',
    version='0.1.18',
    description="Python package for Verifone",
    long_description=readme + '\n\n' + history,
    author="Jaana Sarajärvi",
    author_email='jaana.sarajarvi@vilkas.fi',
    url='https://github.com/vilkasgroup/Verifone',
    packages=find_packages(include=['verifone']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='verifone',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
