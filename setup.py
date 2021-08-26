from distutils.core import setup

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
        'Programming Language :: Python :: 3.9'
    ],
    py_modules=['latexpkges3'],
    entry_points={
        'console_scripts': [
            'latexpkges3=latexpkges3:main',
        ],
    }
)
