#!/usr/bin/env python3
'''Use this to install module'''
from os import path
from setuptools import setup, find_packages

version = '1.1.4'
this_dir = path.abspath(path.dirname(__file__))
with open(path.join(this_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='face-compare',
    version=version,
    description='Compare if two faces are from the same person.',
    author='Matt Lyon',
    author_email='matthewlyon18@gmail.com',
    url='https://github.com/mattlyon93/face-comparison',
    download_url=f'https://github.com/mattlyon93/face-comparison/archive/v{version}.tar.gz',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.7',
    license='MIT License',
    packages=find_packages(),
    install_requires=['numpy', 'tensorflow==2.9.3', 'scipy', 'opencv-python'],
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Unix',
        'Operating System :: MacOS',
    ],
    scripts=['bin/compare_faces.py'],
    keywords=['ai', 'cv', 'computer-vision', 'face-detection'],
    include_package_data=True,
)
