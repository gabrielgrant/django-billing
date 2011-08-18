from setuptools import setup

setup(
    name='django-billing',
    version='0.1.1dev',
    author='Gabriel Grant',
    packages=[
        'billing',
        'billing.processor',
        'billing.processor.simple_account',
        'billing.tests',
    ],
    license='LGPL',
    long_description=open('README').read(),
    install_requires=[
        'python-pricing',
        'django-annoying',
        'django-model-utils',
        'South',
        'django-jsonfield',
        'ordereddict',
    ],
    dependency_links = [
    	'http://github.com/gabrielgrant/python-pricing/tarball/master#egg=python-pricing',
    ]
)
