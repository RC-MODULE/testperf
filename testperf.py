
import os
import sys
import shutil
import argparse
import subprocess

from doxy import doxy
from tests_generator import perf_tests_generator


def get_tests_names(cmd_args):
    dirs_names = [name for name in os.listdir(cmd_args.path_to_tests) if 'perf_' in name]
    if not dirs_names:
        print("Perf tests were not found\n")
    return dirs_names


def config_tests(cmd_args):
    try:
        doxy.make_xml(parsed_cmd_args.path_to_inc)
    except FileExistsError as err:
        return
    perf_tests_generator.generate_perf_tests_from_all_xml(parsed_cmd_args)


def run_tests(cmd_args):
    dirs_names = get_tests_names(cmd_args)
    for dir_name in dirs_names:
        os.chdir(dir_name)
        with open('{}.md'.format(dir_name[5:]), 'w') as md_file:
            return_code = subprocess.call(['make', 'run'], stdout=md_file, stderr=subprocess.STDOUT)
            status = '[OK]'
            if return_code != 0:
                status = '[FAIL]'
            print('{} test starting{}{}\n'.format(dir_name[5:], ' ' * (47 - len(dir_name[5:]) + 14), status))
        os.chdir('..')


def gather_output_files(cmd_args):
    extensions_names = ['.md', '.h']
    dirs_names = get_tests_names(cmd_args)
    if not dirs_names:
        return
    tbl_name = os.path.join(cmd_args.path_to_tables, 'tables')
    try:
        os.mkdir(tbl_name)
    except OSError:
        pass
    for dir_name in dirs_names:
        for file_name in os.listdir(dir_name):
            for ext_name in extensions_names:
                if ext_name in file_name:
                    shutil.copy(os.path.join(dir_name, file_name), tbl_name)


def config_and_run(cmd_args):
    config_tests(cmd_args)
    run_tests(cmd_args)
    #gather_output_files(cmd_args)


def parse_cmd_args():
    args_parser = argparse.ArgumentParser()
    subparsers = args_parser.add_subparsers()
    config_parser = subparsers.add_parser('config')
    run_parser = subparsers.add_parser('run')
    out_parser = subparsers.add_parser('outdir')
    all_parser = subparsers.add_parser('all')

    args_parser.add_argument('--path_to_xml', default=os.path.join('doxy', 'xml'), help='Path following which the '
                                                                                        ' generator will find xml'
                                                                                        ' after doxygen work')
    args_parser.add_argument('--path_to_tests', default='.', help='Path following which'
                                                                  ' the generator will make perf tests')
    args_parser.add_argument('--path_to_log', default='.', help='Path following which the generator will make logs')

    config_parser.add_argument('-i', '--path_to_inc', required=True, help='Path to include dir')
    config_parser.add_argument('-b', '--path_to_build', required=True, help='Path to build dir')
    config_parser.add_argument('-p', '--point', default='float', help=('It can take a value = float',
                                                                       '(perf tests for floating point)',
                                                                       ' or fixed(perf tests for fixed)'))

    all_parser.add_argument('-i', '--path_to_inc', required=True, help='Path to include dir')
    all_parser.add_argument('-b', '--path_to_build', required=True, help='Path to build dir')
    all_parser.add_argument('-p', '--point', default='float', help=('It can take a value = float',
                                                                       '(perf tests for floating point)',
                                                                       ' or fixed(perf tests for fixed)'))

    out_parser.add_argument('-t', '--path_to_tables', default='.', help='Path to a dir with perf tables')

    config_parser.set_defaults(func=config_tests)
    run_parser.set_defaults(func=run_tests)
    out_parser.set_defaults(func=gather_output_files)
    all_parser.set_defaults(func=config_and_run)

    console_args = args_parser.parse_args(sys.argv[1:])

    return console_args

parsed_cmd_args = parse_cmd_args()
parsed_cmd_args.func(parsed_cmd_args)









