#######################################################
# Software designer: A.Brodyazhenko
# Year: 2019
# Content: Functions for managing testperf
#######################################################

import os
import shutil
import subprocess

from doxy import manager as doxy_manager
from generators.cpptests import CpptestsGenerator


def determine_cpptests_dirs_names(testperf_cmd_keys):
    dirs_names = [name for name in os.listdir(testperf_cmd_keys.path_to_cpptests) if 'perf_' in name]
    if not dirs_names:
        print("Perf tests were not found\n")
    return dirs_names


def configure_cpptests(testperf_cmd_keys):
    try:
        doxy_manager.make_doxy_xml(testperf_cmd_keys.path_to_headers)
    except FileExistsError:
        return
    cpptests_generator = CpptestsGenerator(testperf_cmd_keys.path_to_build,
                                           testperf_cmd_keys.path_to_doxy_xml,
                                           testperf_cmd_keys.point_type)
    cpptests_generator.generate_cpptests_from_some_doxy_xml()


def run_cpptests(testperf_cmd_keys):
    dirs_names = determine_cpptests_dirs_names(testperf_cmd_keys)
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


def delete_cpptests(testperf_cmd_keys):
    perf_test_list = [perf_test_name for perf_test_name in os.listdir() if 'perf_' in perf_test_name]
    if not perf_test_list:
        print("Perf tests weren't found!")
        return
    for perf_test in perf_test_list:
        shutil.rmtree(perf_test)
        print('remove {}'.format(perf_test))


def configure_and_run_cpptests(testperf_cmd_keys):
    configure_cpptests(testperf_cmd_keys)
    run_cpptests(testperf_cmd_keys)
    run_cpptests(testperf_cmd_keys)


def gather_output_files(testperf_cmd_keys):
    dirs_names = determine_cpptests_dirs_names(testperf_cmd_keys)
    if not dirs_names:
        return
    table_name = os.path.join(testperf_cmd_keys.path_to_tables, 'tables')
    log_name = os.path.join(testperf_cmd_keys.path_to_tables, 'failed_tests_logs')
    try:
        os.mkdir(table_name)
    except FileExistsError:
        pass
    try:
        os.mkdir(log_name)
    except FileExistsError:
        pass
    for dir_name in dirs_names:
        files_in_test = os.listdir(dir_name)
        try:
            md_file = files_in_test[files_in_test.index(dir_name[5:] + '.md')]
            shutil.copy(os.path.join(dir_name, md_file), table_name)
        except ValueError:
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
    print("Results of tests running were gathered in {}".format(table_name))

if __name__ == '__main__':
    pass
