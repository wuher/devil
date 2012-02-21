from distutils.core import setup

setup(
    name='devil',
    version='0.4',
    author='Janne Kuuskeri (wuher)',
    author_email='janne.kuuskeri@gmail.com',
    url='https://github.com/wuher/devil/',
    packages=['devil', 'devil.perm', 'devil.mappers'],
    install_requires=['simplejson>=2.1.0', 'django>=1.3.0'],
    license='MIT',
    description='Simple REST framework for Django',
    long_description=open('README.markdown').read(),
)
