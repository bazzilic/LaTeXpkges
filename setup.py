from distutils.core import setup
import py2exe

setup(
    name='latexpkges3',
    version='0.2',
    description='utility for cleaning unused LaTeX packages',
    url='https://github.com/TarasKuzyo/LaTeXpkges',
    author='Taras Kuzyo',
    license='MIT',
    keywords='tools cleanup LaTeX',
    python_requires=">=3.5",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    package_dir={'': 'latexpkges3'},
    options={
        'py2exe': {'bundle_files': 1, 'compressed': True}
    },
    entry_points={
        'console_scripts': [
            'latexpkges3=latexpkges3:main',
        ],
    }
)
