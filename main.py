
import os
import sys
import shutil
import argparse
import subprocess

from doxy import manager
from generators.cpptests import CpptestsGenerator


def get_cpptests_dirs_names(cmd_args):
    dirs_names = [name for name in os.listdir(cmd_args.path_to_cpptests) if 'perf_' in name]
    if not dirs_names:
        print("Perf tests were not found\n")
    return dirs_names


def configure_cpptests(cmd_args):
    try:
        manager.make_doxy_xml(parsed_cmd_args.path_to_headers)
    except FileExistsError as err:
        return
    cpptests_generator = CpptestsGenerator(cmd_args.path_to_build, cmd_args.path_to_doxy_xml)
    cpptests_generator.generate_cpptests_from_some_doxy_xml()


def run_cpptests(cmd_args):
    dirs_names = get_cpptests_dirs_names(cmd_args)
    for dir_name in dirs_names:
        os.chdir(dir_name)
        status = '[OK]'
        info_about_log = 'There is information about this perf test starting in {}.log'.format(dir_name[5:])
        with open('{}.log'.format(dir_name[5:]), 'w') as output_file:
            print('-----------------------------------------------------')
            print('Starting the perf test for {}...'.format(dir_name[5:]))
            return_code = subprocess.call(['make', 'run'], stdout=output_file, stderr=subprocess.STDOUT)
        if return_code != 0:
            status = '[FAIL]'
        else:
            with open('{}.log'.format(dir_name[5:]), 'r') as output_file:
                out_after_make = output_file.read()
            try:
                begin = out_after_make.index('/**')
                end = out_after_make.index(');')
                out_after_make = out_after_make[begin:end + 2]

                with open('{}.md'.format(dir_name[5:]), 'w') as md_file:
                    md_file.write(out_after_make)

                info_about_log = 'There are perf tables in {}.md'.format(dir_name[5:])
            except ValueError:
                status = 'Warning! [OK]'
                print('Warning! The perf table for {} was not found!'.format(dir_name[5:]))
        os.chdir('..')
        print('The perf test for {} {}{}'.format(dir_name[5:], ' ' * (47 - len(dir_name[5:]) + 18), status))
        print(info_about_log)
        print('-----------------------------------------------------')


def gather_output_files(cmd_args):
    dirs_names = get_cpptests_dirs_names(cmd_args)
    if not dirs_names:
        return
    table_name = os.path.join(cmd_args.path_to_tables, 'tables')
    log_name = os.path.join(cmd_args.path_to_tables, 'failed_tests_logs')
    try:
        os.mkdir(table_name)
    except FileExistsError:
        # shutil.rmtree(tbl_name)
        # os.mkdir(tbl_name)
        pass
    try:
        os.mkdir(log_name)
    except FileExistsError:
        # shutil.rmtree(log_name)
        # os.mkdir(log_name)
        pass
    for dir_name in dirs_names:
        files_in_test = os.listdir(dir_name)
        try:
            md_file = files_in_test[files_in_test.index(dir_name[5:] + '.md')]
            shutil.copy(os.path.join(dir_name, md_file), table_name)
        except ValueError as value_error:
            try:
                log_file = files_in_test[files_in_test.index(dir_name[5:] + '.log')]
                shutil.copy(os.path.join(dir_name, log_file), log_name)
            except ValueError:
                print('{0} was not found!'.format(dir_name[5:] + '.log'))
    os.chdir('tables')
    for md_file in [file for file in os.listdir() if '.md' in file]:
        try:
            os.rename(md_file, md_file[:-3] + '.h')
        except FileExistsError:
            os.replace(md_file, md_file[:-3] + '.h')
    os.chdir('..')


def kill_cpptests(cmd_args):
    perf_test_list = [perf_test_name for perf_test_name in os.listdir() if 'perf_' in perf_test_name]
    if not perf_test_list:
        print("Perf tests weren't found!")
        return
    for perf_test in perf_test_list:
        shutil.rmtree(perf_test)
        print('remove {}'.format(perf_test))


def configure_and_run_cpptests(cmd_args):
    configure_cpptests(cmd_args)
    run_cpptests(cmd_args)
    #gather_output_files(cmd_args)


def parse_cmd_args():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--path_to_tests', default='.', help='Path following which'
                                                                  ' the generator will make perf tests')
    args_parser.add_argument('--path_to_doxy_xml', default=os.path.join('doxy', 'xml'), help='Path following which the '
                                                                                             ' generator will find xml'
                                                                                             ' after doxygen work')
    args_parser.add_argument('--path_to_log', default='.', help='Path following which the generator will make logs')

    subparsers = args_parser.add_subparsers()
    config_parser = subparsers.add_parser('config')
    config_parser.add_argument('-i', '--path_to_headers', required=True, help='Path to include dir')
    config_parser.add_argument('-b', '--path_to_build', required=True, help='Path to build dir')
    config_parser.add_argument('-p', '--point_type', default='float', help=('It can take a value = float',
                                                                            '(perf tests for floating point)',
                                                                            ' or fixed(perf tests for fixed)'))
    config_parser.set_defaults(func=configure_cpptests)

    run_parser = subparsers.add_parser('run')
    run_parser.set_defaults(func=run_cpptests)

    kill_parser = subparsers.add_parser('kill')
    kill_parser.set_defaults(func=kill_cpptests)

    out_parser = subparsers.add_parser('outdir')
    out_parser.add_argument('-t', '--path_to_tables', default='.', help='Path to a dir with perf tables')
    out_parser.set_defaults(func=gather_output_files)

    all_parser = subparsers.add_parser('all')
    all_parser.add_argument('-i', '--path_to_headers', required=True, help='Path to include dir')
    all_parser.add_argument('-b', '--path_to_build', required=True, help='Path to build dir')
    all_parser.add_argument('-p', '--point_type', default='float', help=('It can take a value = float',
                                                                         '(perf tests for floating point)',
                                                                         ' or fixed(perf tests for fixed)'))
    all_parser.set_defaults(func=configure_and_run_cpptests)

    cmd_args = args_parser.parse_args(sys.argv[1:])

    return cmd_args

parsed_cmd_args = parse_cmd_args()
parsed_cmd_args.func(parsed_cmd_args)









