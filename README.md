# LaTeXpkges
This is a LaTeX package cleanup utility. Use it to find packages that are included in your LaTeX document but are not actually used.

**NEW:** You may now run it directly against your original sources! The utility **will not changes** the sources while working. 

## How it Works
The utility follows the following algorithm:

1. Find all package imports in the LaTeX document
2. Exclude them one by one
3. Rebuild the project
4. Check whether the PDF changes

The idea is that if after you excluded the package, the PDF did not change, then it is safe to remove that package. In the end, the utility suggests a list of packages that it deems safe to remove.

PDFs are compared using MD5 hash after being stripped of ID's and dates. XDV files are compared with diff.

## General Assumptions
This utility runs on Linux and Windows platforms.

You may use any of the LaTeX engines: `latex`, `pdflatex`,`xelatex` or `lualatex` as a processor and either `bibtex` or `biber` for bibliography.

## Usage
To use the utility, go to the location of your LaTeX project. Assuming your main `.tex` file is `main.tex` and it is in that folder, run the script from the command line:

    LaTeXpkges.py --latex pdflatex --bibtex biber  main.tex

Let it finish, and in the end it will inform you what packages it considers as unused in your project. The flag `--visual` will convert the files (DVX or PDF) into images and compare them, the flag `--debug` will leave behind all temporary files use in the process. 

You may run `LaTeXpkges -h` or `LaTeXpkges --help` for more info.

## Development
This program was initially developed by Vasily Sidorov (@Bazzilic) and the development now continues under Taras Kuzyo with the support of Books in Bytes, Inc.

The program intentionaly handles ONLY packages that are inserted at top level, that is, that are inserted inside the main project
 file and not by file called via ...

   \input 
   \usepackage{}
   \RequirePackage

The reasons for this are:

A- The programming may not be so simple, the logic would be quite messy and it will make the program harder for people to contrib
ute to the project!

B- Potential for creating a messy directory with many copies of many files spread in many subdirectories ... 

C- Confusing logic (to the user) because we definitely do not want the program to follow a 

    \RequirePackage{amsmath}  

and start editing "amsmath" for exclusion of any of its subpackages, even if the user is able to edit it.
