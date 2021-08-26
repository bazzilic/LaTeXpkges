# LaTeXpkges3

This is a LaTeX package cleanup utility. You can use it to find packages that are included in your LaTeX document but are not actually used.

You may run it directly against your original sources. The utility operates on a copy of the original .tex file and **will not modify** any source files while working.

**Note**: it may delete your other LaTeX-related files with the following extensions: `.log`, `.aux`, `.dvi`, `.ps`, `.pdf`, `.xdv`, `.bcf`, `.bbl`, `.blg`.

Current version is based on `python >= 3.6`. If you need a version working for `python < 3.0`, please use the python 2 compatible [release](https://github.com/TarasKuzyo/LaTeXpkges/releases/tag/v0.2). 
## How it Works

### Hash-based algorithm

The utility follows the following algorithm:

1. Find all package imports in the LaTeX document
2. Exclude them one by one
3. Rebuild the project
4. Check whether the PDF changes

The idea is that if after you excluded the package, the PDF did not change, then it is safe to remove that package. In the end, the utility suggests a list of packages that it deems safe to remove.

PDFs are compared using MD5 hash after being stripped of ID's and dates. XDV files are compared with diff.

### Visual algorithm

Alternatively, you may use the flag `--visual` to convert the files (DVX or PDF) into images and compare them one-by-one instead.

Usually, this method is slower than the MD5-based algorithm but can sometimes provide more accurate results. Also, you can speed it up with the multiprocessing enabled.

**Note:** `pdflatex` yields some erratic results for MD5 comparison, so it is better to use it only in the visual mode.

## General Assumptions

This utility runs on Linux and Windows platforms.

You may use any of the LaTeX engines: `latex`, `pdflatex`,`xelatex` or `lualatex` as a processor and either `bibtex` or `biber` for bibliography.

In order to use the visual comparison, you need to have [ghostscript](https://www.ghostscript.com/) installed.

## Usage

To use the utility, go to the location of your LaTeX project. Assuming your main `.tex` file is `main.tex` and it is in that folder, run the script from the command line:

```
latexpkges3 --latex pdflatex --bibtex biber  main.tex
```
### Command-line arguments

`LaTeXpkges3` accepts a single positional argument - the name of the .tex file to analyze and a number of optional arguments listed in the table below:

| Argument       | Description                                                 |
| -------------- | ----------------------------------------------------------- |
|  --latex       | The name of an engine to process .tex files (default: pdflatex). Supported engines: latex, pdflatex, xelatex, lualatex |
|  --bibtex      | The name of a reference engine for .tex files (default: None). Supported engines: bibtex, biber |
|  --num_threads | The number of parallel processes (default: 1)               |
|  --visual      | Do the visual comarison instead of checksum                 |
|  --verbose     | Enable extra verbosity                                      |
|  --debug       | Do not delete build artifacts and .pdf files generated during processing |

You may run `latexpkges3 -h` or `latexpkges3 --help` for more info.

## Development

This program was initially developed by Vasily Sidorov (@Bazzilic) and the development now continues under Taras Kuzyo with the support of Books in Bytes, Inc.

The program intentionaly handles ONLY packages that are inserted at top level, that is, that are inserted inside the main project
 file and not by file called via

```
\input 
\usepackage{}
\RequirePackage
```
The reasons for this are:

- The programming may not be so simple, the logic would be quite messy and it will make the program harder for people to contrib
ute to the project!

- Potential for creating a messy directory with many copies of many files spread in many subdirectories

- Confusing logic (to the user) because we definitely do not want the program to follow a `\RequirePackage{amsmath}` and start editing "amsmath" for exclusion of any of its subpackages, even if the user is able to edit it.
