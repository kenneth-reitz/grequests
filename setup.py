# -*- coding: utf-8 -*-
"""
GRequests allows you to use Requests with Gevent to make asynchronous HTTP
Requests easily.

Usage
-----

Usage is simple::

    import grequests

    urls = [
        'http://www.heroku.com',
        'http://tablib.org',
        'http://httpbin.org',
        'http://python-requests.org',
        'http://kennethreitz.com'
    ]

Create a set of unsent Requests::

    >>> rs = (grequests.get(u) for u in urls)

Send them all at the same time::

    >>> grequests.map(rs)
    [<Response [200]>, <Response [200]>, <Response [200]>, <Response [200]>, <Response [200]>]

"""

from setuptools import setup

setup(
    name='grequests',
    version='0.7.0',
    url='https://github.com/spyoungtech/grequests',
    license='BSD',
    author='Kenneth Reitz',
    author_email='me@kennethreitz.com',
    description='Requests + Gevent',
    long_description=__doc__,
    install_requires=[
        'gevent',
        'requests'
    ],
    tests_require = ['pytest'],
    py_modules=['grequests'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
