"""Template of a setup script for a python project."""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


config = {
    'description': 'Transforms raw data into normalized formats.',
    'author': 'Facebook',
    'url': 'https://github.com/THADEUSH123/design-transformer',
    'download_url': 'https://github.com/THADEUSH123/design-transformer',
    'author_email': 'thadeus.hickman@gmail.com',
    'version': '0.1',
    'install_requires': ['nose', 'geojson', 'pykml',
                         'simplejson', 'pydot'],
    'packages': ['data_transformer'],
    'scripts': [],
    'name': 'data_transformer',
    'entry_points': {'console_scripts':
                     ['data_transformer=data_transformer.__main__:main']}
}

setup(**config)
