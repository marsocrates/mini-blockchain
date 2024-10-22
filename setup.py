from setuptools import setup

setup(
    name='blockchain',
    version='0.1',
    py_modules=['cli','blockchain'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        blockchain=cli:blockchain_poc
    ''',
)