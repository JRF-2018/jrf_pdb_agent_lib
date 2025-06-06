# setup.py
from setuptools import setup
import os

VERSION = "0.1.0"

here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.md')
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='jrf_pdb_agent_lib',
    version=VERSION, 
    author='JRF', 
    description='A library for AI-driven debugging and human-AI collaboration using PDB.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/JRF-2018/jrf_pdb_agent_lib', 

    py_modules=['jrf_pdb_agent_lib'], 

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', 
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    install_requires=[], 
)
