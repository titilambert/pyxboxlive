from pip.req import parse_requirements
from setuptools import setup
from pip.download import PipSession

session = PipSession()
install_reqs = parse_requirements('requirements.txt', session=session)
test_reqs = parse_requirements('test_requirements.txt', session=session)

setup(name='pyxboxlive',
      version='1.0.0',
      description='Get XboxLive data',
      author='Thibault Cohen',
      author_email='titilambert@gmail.com',
      url='http://github.org/titilambert/pyxboxlive',
      package_data={'': ['LICENSE.txt']},
      include_package_data=True,
      packages=['pyxboxlive'],
      entry_points={
          'console_scripts': [
              'pyxboxlive = pyxboxlive.__main__:main'
          ]
      },
      license='Apache 2.0',
      install_requires=[str(r.req) for r in install_reqs],
      tests_require=[str(r.req) for r in test_reqs],
      classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
)
