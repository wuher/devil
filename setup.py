from distutils.core import setup

# import sys
# reload(sys).setdefaultencoding('ascii')

setup(
    name='dRest',
    version='0.1',
    packages=['drest',],
    license='MIT',
    long_description=open('README.markdown').read(),
)