#!/usr/bin/env python

from distutils.core import setup

setup(name='Connect Utils',
      version='1.3',
      description='Trimble Connect Python Utilities',
      author='JCMBsoft',
      author_email='Geoffrey@jcmbsoft.com',
      url='https://jcmbsoft.com/',
      license="MIT For Trimble, GPL V3 for everyone else",
      py_modules=['Connect_Lib'],
      scripts=['Connect_Upload.py','Connect_Download.py'
        ]
     )
