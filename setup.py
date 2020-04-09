from setuptools import setup, find_packages

setup(
    name='git_report',
    version='0.1',
    description='Generate git reports.',
    url='http://github.com/echrisinger/git_report',
    author='Evan Chrisinger',
    author_email='echrisinger@gmail.com',
    license='MIT',
    packages=[
        'git_report'
    ],
    install_requires=[
        'botocore',
        'boto3>=1.9',
        'gevent>=1.3',
        'redis',
        'pytz',
    ],
)
