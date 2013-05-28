# -*- coding: utf-8 -
#
# This file is part of django-tinymce-images released under the MIT license. 
# See the LICENSE for more information.

import os
import sys
from setuptools import setup, find_packages

from tinymce_images import VERSION

setup(
    name='django-tinymce-images',
    version=VERSION,
    description='Plugin to tinymce, Image browser in media folder. With connector to django',
    long_description=file(
        os.path.join(
            os.path.dirname(__file__),
            'README.md'
        )
    ).read(),
    author='Victor Safronovich',
    author_email='vsafronovich@gmail.com',
    license='MIT',
    url='http://github.com/suvit/django-tinymce-images',
    zip_safe=False,
    packages=find_packages(exclude=['docs', 'examples', 'tests']),
    install_requires=['django-tinymce'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Environment :: Web Environment',
        'Topic :: Software Development',
    ]
)
