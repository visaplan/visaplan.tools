# -*- coding: utf-8 -*- vim: et ts=8 sw=4 sts=4 si tw=79 cc=+8
"""Installer for the visaplan.tools package."""

from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])


setup(
    name='visaplan.tools',
    version=open('VERSION').read().strip()
            # +'.dev5'  # in branches only
            ,
    description="General Python tools",
    long_description=long_description,
    # Get more from https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Intended Audience :: Developers",
        "Natural Language :: German",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
    ],
    author='Tobias Herp',
    author_email='tobias.herp@visaplan.com',
    url='https://pypi.org/project/visaplan.tools',
    packages=find_packages('src'),
    namespace_packages=[
        'visaplan',
        ],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
