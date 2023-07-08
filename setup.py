from setuptools import setup, find_packages

setup(
    name='comwatt-client',
    version='0.0.1',
    author='Matéo Greil',
    author_email='contact@greil.fr',
    description='Python Client for Comwatt API',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
