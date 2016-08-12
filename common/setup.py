from setuptools import setup

setup(name='common',
      version='1.0',
      description='Package to interact with VDX REST interface',
      author='Darin Sikanic',
      author_email='dsikanic@brocade.com',
      packages=['common'],
      install_requires=[
          'requests'
      ]
     )
