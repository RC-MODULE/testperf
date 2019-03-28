import os
import sys
import shutil


def copy_doxyfile():
    doxyfile = os.path.join(os.path.dirname(sys.argv[0]), 'doxy', 'Doxyfile')
    try:
        os.mkdir('doxy')
        shutil.copy(doxyfile, 'doxy')
    except FileExistsError:
        shutil.copy(doxyfile, 'doxy')


def write_path_to_doxyfile(include_path):
    with open(os.path.join('doxy', 'Doxyfile'), 'a') as doxyfile:
        doxyfile.write('INPUT = {}'.format(include_path))


def make_xml(include_path):
    copy_doxyfile()
    write_path_to_doxyfile(include_path)
    os.chdir('doxy')
    os.system('doxygen')
    os.chdir('..')