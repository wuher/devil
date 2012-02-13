from distutils.core import setup

setup(
    name='devil',
    version='0.2',
    author='Janne Kuuskeri (wuher)',
    author_email='janne.kuuskeri@gmail.com',
    url='https://github.com/wuher/devil/',
    packages=['devil',],
    license='MIT',
    description='Simple REST framework for Django',
    long_description=open('README.markdown').read(),
)
