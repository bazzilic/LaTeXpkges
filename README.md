# LaTeXpkges
This is a LaTeX package cleanup utility. Use it to find packages that are included in your LaTeX document but are not actually used.

**IMPORTANT:** Do not run it against your original sources! **Copy** the folder and run the utility against the copy! The utility **changes** the sources while working. If something goes wrong, you might be left with your sources changed and/or deleted! _I am not responsible for you losing the work of your life due to a bug in this little script :)_

## How it Works
The utility follows the following algorithm:

1. Find all package imports in the LaTeX document
2. Exclude them one by one
3. Rebuild the project
4. Check whether the PDF changes

The idea is that if after you excluded the package, the PDF did not change, then it is safe to remove that package. In the end, the utility suggests a list of packages that it deems safe to remove.

PDFs are compared using MD5 hash.

## General Assumptions
This utility was written with Windows platform in mind and it was only tested in Windows. It _might_ or _might not_ work on other platforms.

Utility assumes that your LaTeX project is built using the standard `pdflatex`-`bibtex`-`pdflatex`-`pdflatex` sequence.

## Usage
To use the utility, **copy** your LaTeX sources in a temporary location (say, `C:\Users\John Smith\Desktop\My LaTeX Sources`). Assuming your main `.tex` file is `main.tex` and it is in that folder, run the script from `cmd.exe` with the following arguments:

    LaTeXpkges "C:\Users\John Smith\Desktop\My LaTeX Sources" main.tex

Let it finish, and in the end it will inform you what packages it considers as unused in your project.

You may run `LaTeXpkges -h` or `LaTeXpkges --help` for more info.
