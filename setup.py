from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='labrat',
    version='0.1.0',
    description='CIELAB color picker',
    long_description=long_description,
    url='http://jangler.info/code/labrat',
    author='Brandon Mulcahy',
    author_email='brandon@jangler.info',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Graphics',
    ],
    keywords=['cie', 'cielab', 'color', 'lab', 'labrat', 'rgb'],
    packages=find_packages(),
    entry_points={
        'gui_scripts': ['labrat=labrat.app:main']
    }
)
