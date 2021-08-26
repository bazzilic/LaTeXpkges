import re
import sys
import filecmp
import hashlib
import pathlib
import argparse
import tempfile
import itertools
import subprocess
import multiprocessing


rm_ext = [
    '.log', '.aux', '.dvi', '.ps', '.pdf', '.xdv', '.bcf', '.bbl', '.blg', '.run.xml'
]


def setup_parser():

    parser = argparse.ArgumentParser(
        prog='latexpkges3',
        description='latexpkges3 is an utility for cleaning unused LaTeX packages'
    )

    parser.add_argument(
        'filename', type=pathlib.Path,
        help='The name of the main .tex file, which is passed to the engine for compilation'
    )
    parser.add_argument(
        '--latex', default='pdflatex',
        choices=['latex', 'pdflatex', 'xelatex', 'lualatex'],
        help='The name of an engine to process .tex files (default: %(default)s)'
    )
    parser.add_argument(
        '--bibtex', default=None,
        choices=['bibtex', 'biber'],
        help='The name of a reference engine for .tex files (default: %(default)s)'
    )
    parser.add_argument(
        '--num_threads', type=int, default=1,
        help="The number of parallel processes (default: %(default)s)"
    )
    parser.add_argument(
        '--visual', action='store_true',
        help='Do the visual comarison instead of checksum'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help="Enable extra verbosity"
    )
    parser.add_argument(
        '--debug', action='store_true',
        help="Do not delete build artifacts and .pdf files generated during processing"
    )
    return parser


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def compute_md5(filename, latex_engine, blocksize=65536):
    '''
    Get a checksum of a file with some metadata stripped
    '''
    ext_mapping = {
        'latex': '.dvi',
        'xelatex': '.xdv',
        'pdflatex': '.pdf',
        'lualatex': '.pdf'
    }
    # pdflatex puts a timestamp in every PDF
    identifiers = [
        rb"/ID\s*\[.*?\]",
        rb"/CreationDate\s+\(.*?\)"
        rb"/ModDate\s+\(.*?\)"
        rb"TeX output [0-9]{4}\.[0-9]{2}\.[0-9]{2}\:[0-9]{4}"
    ]
    output = filename.with_suffix(ext_mapping[latex_engine])
    contents = output.read_bytes()
    for item in identifiers:
        contents = re.sub(item, b'', contents)

    hasher = hashlib.md5()
    for i in range(0, len(contents), blocksize):
        chunk = contents[i:i + blocksize]
        hasher.update(chunk)
    return hasher.hexdigest()


def burst_jpeg(filename, latex_engine):
    '''
    Convert each page of the resulting output file to a jpeg image.
    Return a path to the temporary folder with images.
    '''
    if latex_engine == 'latex':
        command = ['dvips', filename.with_suffix('.dvi')]
        subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            cwd=filename.parent
        )
        input_name = filename.with_suffix('.ps')
    else:
        input_name = filename.with_suffix('.pdf')

    temp_dir = tempfile.TemporaryDirectory(prefix='.', dir=filename.parent)
    jpg_prefix = pathlib.Path(temp_dir.name) / filename.stem

    command = [
        'gs', '-q', '-dNOPAUSE', '-dBATCH', '-sDEVICE=jpeg',
        f'-sOutputFile={jpg_prefix}-p%05d.jpg', '-r300x300', str(input_name)
    ]
    subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        cwd=filename.parent
    )
    return jpg_prefix.parent


def images_match(src_path, dst_path):
    '''
    Return True if all images in src_path are identical to images in dst_path
    '''
    for src in src_path.glob("*.jpg"):
        dst = dst_path.with_name(src.name)
        if not src.exists() or not dst.exists():
            return False
        if not filecmp.cmp(src, dst):
            return False
    return True


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def split_preamble(text):
    '''
    Split the text into preamble and document body
    '''
    sep = r'\begin{document}'
    preamble, body = text.split(sep, 1)
    return preamble, sep + body


def extract_packages(text):
    '''
    Yields a pair of package name and preamble text with the package import excluded
    '''
    expr = r'(\\usepackage(?:\[[^\]]*\])?\s*\{([a-zA-Z0-9,\s-]+)\})'
    pattern = re.compile(expr, re.MULTILINE)
    for match in pattern.finditer(text):
        parent = match.group(1)
        packages = match.group(2)
        for name in packages.split(','):
            remaining = ",".join(x for x in packages.split(',') if x != name)
            if remaining:
                yield name, text.replace(parent, parent.replace(packages, remaining))
            else:
                yield name, text.replace(parent, '')


def get_packages_list(filenames):
    payload = []
    for path in filenames:
        text = path.read_text()
        preamble, body = split_preamble(text)
        for package, updated_preamble in extract_packages(preamble):
            payload.append((package, updated_preamble + body, path))
    return payload


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def test_package(
        filename, package_name, replacement, latex_engine, bibtex_engine,
        original_jpeg=None, original_md5=None, verbose=False, debug_on=True):

    prefix_path = filename.parent.resolve() / (package_name + '__')
    with tempfile.NamedTemporaryFile(mode='w', prefix=str(prefix_path), suffix='.tex', delete=False) as tmp_file:
        tmp_file.write(replacement)

    this_filename = pathlib.Path(tmp_file.name)

    if build(this_filename, latex_engine, bibtex_engine, bool(original_jpeg)):
        if original_jpeg:
            this_jpeg = burst_jpeg(this_filename, latex_engine)
            if images_match(original_jpeg, this_jpeg):
                result_msg = "OK"
            else:
                result_msg = "Images don't match"
        else:
            this_md5 = compute_md5(this_filename, latex_engine)
            if this_md5 == original_md5:
                result_msg = "OK"
            else:
                result_msg = "Checksum mismatch"
    else:
        result_msg = "Build failed"

    if verbose:
        print(f"Checking '{package_name}' package from {filename.name}.. {result_msg}")

    if not debug_on:
        cleanup(this_filename, original_jpeg)
        this_filename.unlink()

    return result_msg == 'OK'


def build(filename, latex='pdflatex', bibtex=None, visual=False, verbose=False):

    if latex == 'xelatex':
        if visual:
            compile_code = [latex, "-halt-on-error", filename.name]
        else:
            compile_code = [latex, "-no-pdf", "-halt-on-error", filename.name]
    else:
        compile_code = [latex, "-interaction=nonstopmode", "-halt-on-error", filename.name]

    if verbose:
        print('Building the project  ', end='')
    response = subprocess.run(
        compile_code, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        cwd=filename.parent
    )
    if verbose:
        print('.' if response.returncode == 0 else 'F', end='')

    if bibtex:
        response = subprocess.run(
            [bibtex, str(filename.stem)], stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, cwd=filename.parent
        )
        if verbose:
            print('.' if response.returncode == 0 else 'F', end='')
        response = subprocess.run(
            compile_code, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, cwd=filename.parent
        )
        if verbose:
            print('.' if response.returncode == 0 else 'F', end='')

    response = subprocess.run(
        compile_code, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, cwd=filename.parent
    )
    if verbose:
        print('.' if response.returncode == 0 else 'F', end='')

    if verbose:
        print('  Done', end='\n')

    return response.returncode == 0


def cleanup(filename, jpeg_dirname):
    '''
    Remove auxillary files and generated jpg images
    '''
    for ext in rm_ext:
        if filename.with_suffix(ext).exists():
            filename.with_suffix(ext).unlink()
    if jpeg_dirname and jpeg_dirname.exists():
        for item in jpeg_dirname.iterdir():
            item.unlink()
        jpeg_dirname.rmdir()


def main():

    parser = setup_parser()
    args = parser.parse_args()

    # initial build
    success = build(args.filename, args.latex, args.bibtex, args.visual, verbose=args.verbose)
    if not success:
        sys.exit("Initial build failed. Exiting.")

    # baseline
    if args.verbose:
        print('Calculating the baseline summary  ', end='')
    if args.visual:
        original_jpeg = burst_jpeg(args.filename, args.latex)
        original_md5 = None
    else:
        original_md5 = compute_md5(args.filename, args.latex)
        original_jpeg = None
    if args.verbose:
        print('Done')

    # packages to check
    packages = get_packages_list([args.filename])
    if args.verbose:
        print(f'Found {len(packages)} packages in {args.filename.name}')

    # check if can delete each package (parallel)
    arguments = [
        (
            args.filename, package_name, replacement, args.latex, args.bibtex,
            original_jpeg, original_md5, args.verbose, args.debug
        )
        for package_name, replacement, path in packages
    ]
    num_threads = min(max(1, args.num_threads), multiprocessing.cpu_count())
    with multiprocessing.Pool(num_threads) as pool:
        passed = pool.starmap(test_package, arguments)

    # print summary
    targets = list(itertools.compress(packages, passed))
    if targets:
        target_names = ",".join(item[0] for item in targets)
        print(f'The following {len(targets)} package(s) are safe to remove in {args.filename}: {target_names}')
    else:
        print("There are no safe to remove packages")

    if not args.debug:
        cleanup(args.filename, original_jpeg)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


if __name__ == '__main__':
    main()
