from setuptools import setup, find_packages

setup(
    name='db_func_cache',
    version='0.1.0',
    packages=find_packages(exclude=['tests*']),
    install_requires=["dill", "SQLAlchemy>=2.0"],
    author='Brian Dickinson',
    author_email='DickinsonBC@gcc.edu',
    description='Simple function decorator to cache function args->return in a database',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/brian-dickinson/db-func-cache',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.12',
)