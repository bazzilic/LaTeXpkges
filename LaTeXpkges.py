#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import os
import sys
import filecmp
import fileinput
import hashlib
import subprocess
import random
import argparse
from glob import glob


def get_basename(s):
    return os.path.splitext(s)[0]


def get_variants(s):

    # find where comment starts
    comment_ptrn = re.compile(r'([^\\]|^)%')
    comment_match = re.search(comment_ptrn, s)
    comment_start = len(s)
    # ignore comments line
    if comment_match:
        comment_start = comment_match.start()
    # regex to match packages used
    uspkg_cmd_pttrn = re.compile(r'\\usepackage\s*(?:\[[^\]]*\])?\s*\{([a-zA-Z0-9,\s-]+)\}')
    matches = uspkg_cmd_pttrn.finditer(s)

    for match in matches:
        pkgs = match.group(1) # list of packages in the current \usepackage command
        pkgs_start_pos = match.start(1)
        pkgs_end_pos = match.end(1)

        # match is commented out
        if match.start() > comment_start:
            # print "This is a comment" # DEBUG
            continue

        if pkgs.find(',') == -1: # single package case
            yield (s[pkgs_start_pos:pkgs_end_pos], 
                   s[:max(0,match.start()-1)] + s[match.end():]) # remove the whole \usepackage command
        else: # multiple packages case
            separators = find_all(pkgs, ',')
            last_comma_index = 0

            for sep in separators:
                yield (s[pkgs_start_pos+last_comma_index:pkgs_start_pos+sep], 
                       s[:pkgs_start_pos+last_comma_index] + s[pkgs_start_pos+sep+1:])
                last_comma_index = sep + 1

            # last package
            yield (s[pkgs_start_pos+last_comma_index:pkgs_end_pos],
                   s[:pkgs_start_pos+last_comma_index-1] + s[pkgs_end_pos:])


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches


def substitute_line_in_file(input_name, output_name, line_no, new_str): # line_no is 1-based


    with open(input_name, 'r') as fp:
        lines = fp.readlines()
    # write all lines from the input_name to 
    # the output_name with changing a line with 
    # number line_no to new_str
    with open(output_name, 'w') as fp:
        for i, line in enumerate(lines, start=1):
            if i == line_no:
                fp.write(new_str)
            else:
                fp.write(line)




def build(filename, latex='pdflatex', visual=False, bibtex=None, dbgout=False):
    if dbgout:
        sys.stdout.write("Building the project.")
        sys.stdout.flush()

    compile_code = [latex, "-interaction=nonstopmode", "-halt-on-error", filename]
    if latex == 'xelatex':
        if visual:
            compile_code = [latex, "-halt-on-error", filename]
        else:
            compile_code = [latex, "-no-pdf", "-halt-on-error", filename]

    code = 0
    with open(os.devnull, 'w') as FNULL:
        code = code + subprocess.call(compile_code, stdout=FNULL, stderr=subprocess.STDOUT)  
        if dbgout:
            sys.stdout.write(".")
            sys.stdout.flush()

        if bibtex:
            code = code + subprocess.call([bibtex, get_basename(filename)], 
                                          stdout=FNULL, stderr=subprocess.STDOUT)
            if dbgout:
                sys.stdout.write(".")
                sys.stdout.flush()
            code = code + subprocess.call(compile_code, stdout=FNULL, stderr=subprocess.STDOUT)
            if dbgout:
                sys.stdout.write(".")
                sys.stdout.flush()

        code = code + subprocess.call(compile_code, stdout=FNULL, stderr=subprocess.STDOUT)

    if dbgout:
        print(" Done!")

    return code == 0


def file_md5(path, blocksize=65536):
    hasher = hashlib.md5()

    contents = None
    with open(path, 'rb') as infile:
        contents = infile.read()

    # pdflatex puts a timestamp in every PDF
    re_ID = re.compile(r"/ID\s*\[.*?\]") 
    re_Creation = re.compile(r"/CreationDate\s+\(.*?\)")
    re_Mod = re.compile(r"/ModDate\s+\(.*?\)")

    re_Output = re.compile(r"TeX output [0-9]{4}\.[0-9]{2}\.[0-9]{2}\:[0-9]{4}")

    contents = re.sub(re_ID, '', contents)
    contents = re.sub(re_Creation, '/CreationDate ()', contents)
    contents = re.sub(re_Mod, '/ModDate ()', contents)
    contents = re.sub(re_Output, 'TeX output', contents)

    for chunk in [contents[i:i+blocksize] for i in range(0, len(contents), blocksize)]:
        hasher.update(chunk)

    return hasher.hexdigest()


def find_occurences(main_file):

    occurences = []
    tex_files = [main_file]
    if len(tex_files) == 0:
        return
    for line in fileinput.input(tex_files):
        if line.find("usepackage") != -1:
            occ = {}
            occ['filename'] = fileinput.filename()
            occ['line_no'] = fileinput.filelineno()
            occ['string'] = line
            occurences.append(occ)

    return occurences



def burst_jpeg(filename, latex_engine):

    name = get_basename(filename)
    if latex_engine != 'latex':
        command = "gs -q -dNOPAUSE -dBATCH -sDEVICE=jpeg -sOutputFile={0}-p%04d.jpg -r300x300 {0}.pdf".format(name)
    else:
        with open(os.devnull, 'w') as FNULL:
            subprocess.call(['dvips', filename.replace('.tex', '.dvi')], 
                            stdout=FNULL, stderr=subprocess.STDOUT)  

        command = "gs -q -dNOPAUSE -dBATCH -sDEVICE=jpeg -sOutputFile={0}-p%04d.jpg -r300x300 {0}.ps".format(name)

    os.system(command)


def compare_jpeg(src_name, dst_name):

    count = len(glob("{0}-p*.jpg".format(dst_name)))
    for i in range(1, count+1):
        src = '{0}-p{1:04d}.jpg'.format(src_name, i)
        dst = '{0}-p{1:04d}.jpg'.format(dst_name, i)
        if not os.path.exists(src) or not os.path.exists(dst):
            return False
        if not filecmp.cmp(src, dst):
            return False

    return True



if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='LaTeXpkges', 
                description='LaTeXpkges is a package cleanup utility for LaTeX.')

    parser.add_argument('filename', help='Name of the main .tex file, which is passed to pdflatex for compilation')
    parser.add_argument('--debug', action='store_true', default=False, 
                        help="Don't delete output *.tex and *.pdf files during processing (default: %(default)s)")
    parser.add_argument('--latex', required=False, choices=['latex', 'pdflatex', 'xelatex', 'lualatex'], 
                        default='pdflatex', help='An engine to process .tex files (default: %(default)s)')
    parser.add_argument('--bibtex', required=False, choices=['bibtex', 'biber'], 
                        default=None, help='A reference engine for .tex files (default: %(default)s)')
    parser.add_argument('--visual', action='store_true', default=False, 
                        help="Do the visual comarison instead of checksum (default: %(default)s)")
    parser.add_argument('--input', action='append', required=False, type=str, default=[],
                        help="Specify additional files loaded via \input{} in the document to consider for testing")
    args = parser.parse_args()

    latex_engine  = args.latex
    bibtex_engine = args.bibtex

    ext_mapping = {'latex'   : '.dvi',
                   'xelatex' : '.xdv',
                   'pdflatex': '.pdf', 
                   'lualatex': '.pdf'}

    file_ext = ext_mapping[latex_engine]
    filename = os.path.basename(args.filename)
    filepath = os.path.dirname(args.filename)
    out_file = filename.replace('.tex', file_ext)
    debug_on = args.debug
    visual   = args.visual
    inputs   = args.input

    #if latex_engine == 'xelatex':
    #    print("Comparison using xelatex does not work yet because of wildly different PDF files produced by xelatex")
    #    sys.exit()


    if filepath:
        os.chdir(filepath)

    if not os.path.exists(filename):
        print "The file", filename, "does not exist"
        print "Try to run  LaTeXpkges --help"
        print
        sys.exit()

    if not build(filename, latex_engine, visual, bibtex_engine, dbgout=True):
        print "Initial build fails! Finishing now..."
        sys.exit()

    if visual:
        burst_jpeg(filename, latex_engine)
    else:
        print "Calculating the original checksum for " + out_file + "..."
        original_md5 = file_md5(out_file)
        print "MD5 for the original output file is", original_md5

	occurences = find_occurences(filename)
	for s in inputs:
		occurences.extend(find_occurences(s))
	print len(occurences), "were found."

    packages_to_delete = []
    count = 1
    for occ in occurences:
        for (pkg, variant) in get_variants(occ['string']):
            print "Testing if", pkg, "can be removed...",
            tmp_file = occ['filename'].rsplit('.', 1)[0] + "-LaTeXpkges-{0:03d}.tex".format(count)
            substitute_line_in_file(occ['filename'], tmp_file, occ['line_no'], variant)
            output_file = tmp_file.replace('.tex', file_ext)
            if build(tmp_file, latex_engine, visual, bibtex_engine): 
                if visual:
                    burst_jpeg(tmp_file, latex_engine)
                    res = compare_jpeg(get_basename(filename), get_basename(tmp_file))
                    if res:    
                        packages_to_delete.append(pkg)
                        print "Yep."
                    else:
                        print "Nope. Images don't match"
                else:
                    new_md5 = file_md5(output_file)   
                    # check for a match
                    if new_md5 == original_md5:    
                        packages_to_delete.append(pkg)
                        print "Yep."
                    else:
                        print "Nope. Checksum mismatch:", new_md5
            else:
                print "Nope. Build fails."

            count = count + 1
            if not debug_on:

                if visual:
                    for name in glob("{0}-*.jpg".format(get_basename(tmp_file))):
                        os.remove(name)

                rm_ext = ['.tex', '.log', '.aux', '.dvi', '.ps', '.pdf', '.xdv']
                for ext in rm_ext:
                    fname = tmp_file.replace('.tex', ext)
                    os.remove(fname) if os.path.exists(fname) else None


    if not debug_on and visual:
       for name in glob("{0}-*.jpg".format(get_basename(filename))):
          os.remove(name)
    if not debug_on:
        rm_ext = ['.log', '.aux', '.dvi', '.ps', '.pdf', '.xdv']
        for ext in rm_ext:
            fname = filename.replace('.tex', ext)
            os.remove(fname) if os.path.exists(fname) else None

    print
    if packages_to_delete:
        print "It looks like it's safe to remove these packages:"
        for pkg in packages_to_delete:
            print "\t"+pkg
    else:
        print "We didn't find packages that are safe to remove."


