# -*- coding: utf-8 -*-

import re
import os
import sys
import fileinput
import hashlib
import subprocess
import random
import argparse
from glob import glob

MAIN_FILE = 'Thesis.tex'
PDF_FILE = 'Thesis.pdf'
PATH = os.path.join('.','qwerty')

original_md5 = ''

occurences = []
packages_to_delete = []

def list_all_tex_files(path='.'):
    return [y for x in os.walk(path) for y in glob(os.path.join(x[0], '*.tex'))]

def get_variants(str):
    # print 'The string is', '`'+str+'`' # DEBUG

    # find where comment starts
    comment_ptrn = re.compile(r'([^\\]|^)%')
    comment_match = re.search(comment_ptrn, str)
    comment_start = len(str)
    if comment_match:
        comment_start = comment_match.start()

    uspkg_cmd_pttrn = re.compile(r'\\usepackage\s*(?:\[[^\]]*\])?\s*\{([a-zA-Z0-9,\s-]+)\}')
    matches = uspkg_cmd_pttrn.finditer(str)

    for match in matches:
        pkgs = match.group(1) # list of packages in the current \usepackage command
        pkgs_start_pos = match.start(1)
        pkgs_end_pos = match.end(1)
        # print "big match start", match.start(),  "; end", match.end(),  "; match:", '`'+match.group()+'`' # DEBUG
        # print "sml match start", match.start(1), "; end", match.end(1), "; match:", '`'+match.group(1)+'`' # DEBUG

        if match.start() > comment_start:
            # print "This is a comment" # DEBUG
            continue

        if pkgs.find(',') == -1: # single package case
            yield (str[pkgs_start_pos:pkgs_end_pos], str[:max(0,match.start()-1)] + str[match.end():]) # remove the whole \usepackage command
        else: # multiple packages case
            separators = find_all(pkgs, ',')
            last_comma_index = 0

            for sep in separators:
                yield (str[pkgs_start_pos+last_comma_index:pkgs_start_pos+sep], str[:pkgs_start_pos+last_comma_index] + str[pkgs_start_pos+sep+1:])
                last_comma_index = sep + 1

            # last package
            yield (str[pkgs_start_pos+last_comma_index:pkgs_end_pos], str[:pkgs_start_pos+last_comma_index-1] + str[pkgs_end_pos:])

def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches

def substitute_line_in_file(path, line_no, new_str): # line_no is 1-based
    bak_ext = '.bak'+str(random.randint(1000,9999))
    input_object = fileinput.input(path, inplace=True, backup=bak_ext)
    for line in input_object:
        if fileinput.filelineno() == line_no:
            print new_str.rstrip("\n\r")
        else:
            print line.rstrip("\n\r")

    return path+bak_ext

def build(dbgout=False):
    if dbgout:
        sys.stdout.write("Building the project.")
        sys.stdout.flush()

    code = 0

    with open(os.devnull, 'w') as FNULL:
        code = code + subprocess.call(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                       MAIN_FILE[:-4]], stdout=FNULL, stderr=subprocess.STDOUT)  # cut off the `.tex` ext
        if dbgout:
            sys.stdout.write(".")
            sys.stdout.flush()
        code = code + subprocess.call(["bibtex", MAIN_FILE[:-4]], stdout=FNULL, stderr=subprocess.STDOUT)
        if dbgout:
            sys.stdout.write(".")
            sys.stdout.flush()
        code = code + subprocess.call(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                       MAIN_FILE[:-4]], stdout=FNULL, stderr=subprocess.STDOUT)
        if dbgout:
            sys.stdout.write(".")
            sys.stdout.flush()
        code = code + subprocess.call(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                       MAIN_FILE[:-4]], stdout=FNULL, stderr=subprocess.STDOUT)

    if dbgout:
        print(" Done!")

    return (code == 0) and os.path.exists(PDF_FILE)

def file_md5(path=PDF_FILE, blocksize=65536):
    hasher = hashlib.md5()

    contents = None
    with open(path, 'rb') as infile:
        contents = infile.read()

    re_ID = re.compile(r'/ID\s+\[<[0-9A-Fa-f]+>\s+<[0-9A-Fa-f]+>\]\s+>>') # pdflatex puts a timestamp in every PDF
    re_Creation = re.compile(r'/CreationDate\s+\(D:[0-9+\'-]+\)')
    re_Mod = re.compile(r'/ModDate\s+\(D:[0-9+\'-]+\)')

    contents = re.sub(re_ID, '', contents)
    contents = re.sub(re_Creation, '/CreationDate ()', contents)
    contents = re.sub(re_Mod, '/ModDate ()', contents)

    for chunk in [contents[i:i+blocksize] for i in range(0, len(contents), blocksize)]:
        hasher.update(chunk)

    return hasher.hexdigest()

def find_occurences(path='.'):
    global occurences
    tex_files = list_all_tex_files(path)
    if len(tex_files) == 0:
        return
    for line in fileinput.input([os.path.join(path, name) for name in tex_files]):
        if line.find("usepackage") != -1:
            occ = {}
            occ['filename'] = fileinput.filename()
            occ['line_no'] = fileinput.filelineno()
            occ['string'] = line
            occurences.append(occ)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='LaTeXpkges', description='LaTeXpkges is a package cleanup utility for LaTeX.')
    parser.add_argument('path', help='Path to the folder (!) with your LaTeX files')
    parser.add_argument('name', help='Name of the main .tex file, which is passed to pdflatex for compilation')

    args = parser.parse_args()

    PATH = vars(args)['path']
    if PATH[-1] != os.sep:
        PATH = PATH + os.sep
    if not os.path.isdir(PATH):
        print "Path is required to be a directory, which the supplied first argument is not!"
        print "Try to run  LaTeXpkges --help"
        print
        exit()

    os.chdir(PATH)

    MAIN_FILE = vars(args)['name']

    if not os.path.exists(MAIN_FILE):
        print "The file", MAIN_FILE, "does not exist in directory", PATH
        print "Try to run  LaTeXpkges --help"
        print
        exit()

    PDF_FILE = MAIN_FILE[:-3] + 'pdf'

    if not build(dbgout=True):
        print "Initial build fails! Finishing now..."
        exit()

    print "Calculating the original checksum for " + PDF_FILE + "..."
    original_md5 = file_md5()
    print "MD5 for the original PDF is", original_md5

    print "Looking for package imports in the files...",
    find_occurences()
    print len(occurences), "were found."

    for occ in occurences:
        for (pkg, variant) in get_variants(occ['string']):
            print "Testing if", pkg, "can be removed...",
            tmp_file = substitute_line_in_file(occ['filename'], occ['line_no'], variant)
            if build():                        # I don't remember lazy evaluation
                new_md5 = file_md5()           #
                if new_md5 == original_md5:    # rules in python :)
                    packages_to_delete.append(pkg)
                    print "Yep."
                else:
                    print "Nope. Checksum mismatch:", new_md5
            else:
                print "Nope. Build fails."
            os.remove(occ['filename']) # on Windows you can't rename if the dst exists
            os.rename(tmp_file, occ['filename'])
            os.remove(PDF_FILE) if os.path.exists(PDF_FILE) else None

    print
    if len(packages_to_delete) > 0:
        print "It looks like it's safe to remove these packages:"
        for pkg in packages_to_delete:
            print "\t"+pkg
    else:
        print "We didn't find packages that are safe to remove."
