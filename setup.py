from setuptools import setup, find_packages

setup(
    name='git_report',
    version='0.1',
    description='Generate git reports and have them sent back to your command line.',
    url='http://github.com/echrisinger/git_report',
    author='Evan Chrisinger',
    author_email='echrisinger@gmail.com',
    license='MIT',
    packages=[
        'git_report'
    ],
    scripts=[
        'bin/git-report',
        'bin/handler',
    ],
    install_requires=[
        'awscli',
        'botocore',
        'boto3>=1.9',
        'gevent==1.4.0',
        'gitpython',
        'pytz',
        'watchdog',
    ],
    extras_require={
        'dev': [
            'autopep8',
            'pylint',
        ]
    }
)
