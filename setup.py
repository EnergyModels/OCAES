from setuptools import setup

setup(name='OCAES',
      version='0.0.9',
      description='Technoeconomic optimization of offshore compressed air energy storage (OCAES) systems',
      url='https://github.com/EnergyModels/OCAES',
      author='Jeff Bennett',
      author_email='jab6ft@virginia.edu',
      license='MIT',
      packages=['OCAES'],
      zip_safe=False,
      install_requires=['pyomo', 'pandas', 'numpy', 'seaborn', 'matplotlib', 'scipy', 'joblib', 'xlrd', 'xlwt'])
