from setuptools import setup, find_packages


setup(name='healthapp',
      version='0.0.1',
      packages=find_packages(),
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'alert-processor = healthapp.alerter:main',
              'agent = healthapp.agent:main',
          ]
      },
      )
