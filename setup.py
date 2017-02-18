from setuptools import setup

setup(
    name = "sissigen",
    py_modules = ['sissigen'],
    version = '0',
    entry_points={
          'console_scripts': [
              'sissigen = sissigen:main'
          ]
      },
)
