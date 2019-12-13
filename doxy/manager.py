import os
import sys
import subprocess
import shutil


def copy_doxyfile():
    doxyfile = os.path.join(os.path.dirname(sys.argv[0]), 'doxy', 'Doxyfile')
    try:
        os.mkdir('doxy')
        shutil.copy(doxyfile, 'doxy')
    except OSError:
        shutil.rmtree(os.path.join('doxy', 'xml'))
        shutil.copy(doxyfile, 'doxy')


def write_path_to_doxyfile(path_to_headers):
    with open(os.path.join('doxy', 'Doxyfile'), 'a') as doxyfile:
        doxyfile.write('INPUT = {}'.format(path_to_headers))


def make_doxy_xml(path_to_headers):
    abs_inc_path = os.path.abspath(path_to_headers)
    if not os.path.exists(abs_inc_path):
        print('-----------------------------------------------------')
        print("Error! Path: '{}' doesn't exist".format(path_to_headers))
        print("The perf tests won't be created!")
        print('-----------------------------------------------------')
        raise FileExistsError
    copy_doxyfile()
    write_path_to_doxyfile(abs_inc_path)
    os.chdir('doxy')
    with open(os.devnull, 'wb') as devnull:
        try:
            subprocess.check_call('doxygen', stdout=devnull, stderr=subprocess.STDOUT)
            print('Doxygen start...\n')
        except Exception as err:
            print(err)
            print('Doxygen start                         [FAIL]\n')
    os.chdir('..')

if __name__ == '__main__':
    pass
