import os
import re
import random
import shutil

import sys
import argparse

from collections import namedtuple

from xml_parser import open_xml
from xml_parser import get_group_name
from xml_parser import get_perf_scripts
from xml_parser import get_funcs_prototypes


def parse_perf_scripts(perf_scripts):
    prf_scs = []
    PerfScripts = namedtuple('PerfScripts', 'perf_params args_names size init deinit')
    for perf_script in perf_scripts:
        try:
            size = perf_script.pop('size')
            size = size.strip()
        except Exception:
            size = None
        try:
            init_func = perf_script.pop('init')
            init_func = init_func.strip()
        except Exception:
            init_func = None
        try:
            deinit_func = perf_script.pop('deinit')
            deinit_func = deinit_func.strip()
        except Exception:
            deinit_func = None
        perf_params_list = []
        for perf_param in perf_script.values():
            perf_param = perf_param.strip()
            perf_param = perf_param.replace(' ', ', ')
            perf_params_list.append(perf_param)
        prf_scs.append(PerfScripts(perf_params_list, list(perf_script.keys()), size, init_func, deinit_func))
    return prf_scs


def parse_funcs_prototypes(prototypes):
    Function = namedtuple('Function', 'rtype name args_names args_types prototype')
    funcs = []
    for func_name in prototypes.keys():
        args = prototypes.get(func_name)
        prototype = '{}{};'.format(func_name, args)
        args = re.sub(r'const ', '', args)
        args = args.lstrip('(')
        args = args.rstrip(')')
        args_types = []
        args_names = []
        if args:
            args_list = args.split(',')
            for arg in args_list:
                try:
                    index = arg.index('=')
                    arg = arg[:index]
                except ValueError:
                    pass
                arg = arg.lstrip()
                if '*' in arg:
                    args_types.append(arg.split('*')[0] + '*')
                    args_names.append(arg.split('*')[1])
                else:
                    args_types.append(arg.split(' ')[0])
                    args_names.append(arg.split(' ')[1])
        name_and_rtype = func_name.split(' ')
        if name_and_rtype[-2] == 'void':
            name_and_rtype[-2] = ''
        else:
            name_and_rtype[-2] = name_and_rtype[-2] + ' retVal = '
        funcs.append(Function(name_and_rtype[-2], name_and_rtype[-1], args_names, args_types, prototype))
    return funcs


def is_float_func(func):
    for arg_type in func.args_types:
        if arg_type.find('f') != -1 or arg_type.find('double') != -1:
            return True
    return False


def copy_build_for_board(board, func, test_dir_func):
    make_dir_name = '_'.join(['make', board])
    if board == 'mc12101':
        nmpu = ''
        if is_float_func(func):
            nmpu = '_nmpu0'
        else:
            nmpu = '_nmpu1'
        make_dir_name += nmpu

    make_dir_func = os.path.join(test_dir_func, make_dir_name)

    try:
        shutil.copytree(os.path.join('templates', make_dir_name), make_dir_func)
    except OSError as error:
        raise error


def generate_perf_tests(functions, perf_scripts, board, group_name, path_to_tests):
    file_beginning = ('#include "nmpp.h"\n'
                      '#include "time.h"\n'
                      '#include "stdio.h"\n'
                      '#include "stdlib.h"\n'
                      '#include "fft.h"\n\n'
                      '#pragma data_section ".data_imu0"\n'
                      '    long long L[2048];\n'
                      '#pragma data_section ".data_imu1"\n'
                      '    long long G[2048];\n'
                      '#pragma data_section ".data_imu2"\n'
                      '    long long im2[2048];\n'
                      '#pragma data_section ".data_imu3"\n'
                      '    long long im3[2048];\n'
                      '#pragma data_section ".data_em0"\n'
                      '    long long em0[2048];\n'
                      '#pragma data_section ".data_em1"\n'
                      '    long long em1[2048];\n\n'
                      )               # for the writting
    init_funcs = []
    funcs_for_test = []
    for func in functions:
        if set(func.args_names) != set(perf_scripts[0].args_names):
            init_funcs.append(func.name + '\n')
            continue
        else:
            funcs_for_test.append(func.name + '\n')
        test_dir_func = os.path.join(path_to_tests, func.name)
        copy_build_for_board(board, func, test_dir_func)
        num = 0
        lists = []    # for the writting
        names = []
        cycles = []  # for the writting
        called_funcs = []
        init_args = []
        print_f = []
        test_name = '{}.cpp'.format(func.name)
        path_to_test = os.path.join(test_dir_func, test_name)
        max_spaces = '  ' * len(func.args_names)
        for pss in perf_scripts:
            called_str = '{}({};\n'.format(func.name, ', '.join(func.args_names))
            init_args_str = ''
            print_f_str = ''
            print_f_args_str = ''
            names_str = ''
            lists_str = ''
            cycles_str = ''  # for the writting
            spaces = '  '
            for pos, perf_param in enumerate(pss.perf_params):
                index = str(num)
                if not perf_param.replace(', ', '').replace('.', '').replace('-', '').replace('0x', '').isdigit():
                    list_type = 'long long*'
                else:
                    list_type = func.args_types[pos]
                perf_param_names = perf_param.split(', ')
                params_count = str(len(perf_param_names))
                params = [''.join(['"', param, '"']) for param in perf_param_names]
                params_str = ', '.join(params)
                lists_str += '{2} list{0}[] = {1};\n'.format(index, ''.join(['{', perf_param, '}']), list_type)
                names_str += 'char* name{}[] = {};\n'.format(index, ''.join(['{', params_str, '}']))
                cycles_str += '{0}for(int i{1} = 0; i{1} < {2}; i{1}++) {3}'.format(spaces, index, params_count, '{\n')
                print_f_str += '{:<13}'.format('%s |')
                print_f_args_str += 'name{0}[i{0}], '.format(index)
                init_args_str += '  {0}{1} = ({2})list{3}[i{3}];\n'.format(max_spaces, ' '.join([func.args_types[pos], func.args_names[pos]]), func.args_types[pos], index)
                spaces += '  '
                num += 1
            if pss.size is not None:
                init_args_str += '  {}int size = {};\n'.format(max_spaces, pss.size)
                size_str = 'size'
            else:
                size_str = ''.join(['atoi(', print_f_args_str.split(', ')[-2], ')'])
            if pss.init is None:
                called_str = '{0}t1 = clock();\n{0}{1});\n{0}t2 = clock();\n'.format(spaces, called_str[:-2])
            elif pss.init is not None and pss.deinit is None:
                called_str = '{0}{2}\n{0}t1 = clock();\n{0}{1});\n{0}t2 = clock();\n'.format(spaces, called_str[:-2], pss.init)
            else:
                called_str = '{0}{2}\n{0}t1 = clock();\n{0}{1});\n{0}t2 = clock();\n{0}{3}\n'.format(spaces, called_str[:-2], pss.init, pss.deinit)
            print_f_str += '{:<13}{}'.format('%d | ', '%0.2f')
            print_f_str = ''.join(['"', print_f_str, r'\n"'])
            printf_f_str = '{0}printf({1}, {2} t2 - t1, (float)(t2 - t1) / {3});\n'.format(spaces, print_f_str, print_f_args_str, size_str)
            lists.append(lists_str)
            cycles.append(cycles_str)
            called_funcs.append(called_str)
            init_args.append(init_args_str)
            names.append(names_str)
            print_f.append(printf_f_str)
        brackets = []
        for i in func.args_types:
            spaces = spaces.replace('  ', '', 1)
            brackets.append(spaces + '}\n')
        try:
            with open(path_to_test, 'w') as file:
                file.write(file_beginning)
                file.writelines(lists)
                file.writelines(names)
                file.write('\nint main()\n{\n  clock_t t1, t2;\n')
                file.write('  printf("{2}**{1}{3}ingroup {0}{1}");\n'.format(group_name, r"\n", r"/", 3 * r"\tmp"[0]))
                for i, cycle in enumerate(cycles):
                    s = '   |   '.join(perf_scripts[i].args_names)
                    file.write('  printf("testperf {}{}");\n'.format(str(i), r"\n"))
                    file.write('  printf("{}   |   {:<13}  |  {}{}");\n'.format(s, 'ticks', 'ticks/elem', r"\n"))
                    file.write('  printf("{}{}");\n'.format('---|---' * (len(perf_scripts[i].args_names) + 1), r"\n"))
                    file.write(cycle)
                    file.write(init_args[i])
                    file.write(called_funcs[i])
                    file.write(print_f[i])
                    file.writelines(brackets)
                file.write('\n')
                file.write('  printf("*/{}");\n'.format(r"\n"))
                file.write('  printf("{}");\n'.format(func.prototype))
                file.write('  return 0;\n}\n')
        except Exception as exc:
            print(path_to_test, exc)
    return init_funcs, funcs_for_test


def parse_cmd_args():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('-b', '--board', default='mc12101')
    args_parser.add_argument('--path_to_xml', default='..')
    args_parser.add_argument('--path_to_tests', default='..')
    args_parser.add_argument('--path_to_tables', default='..')
    args_parser.add_argument('--path_to_log', default='..')
    args_parser.add_argument('--xml_dir_name', default='xml')

    console_args = args_parser.parse_args(sys.argv[1:])

    return console_args


def generate_makefile(path):
    with open(os.path.join(path, "Makefile"), 'w') as file:
        file.write('ALL_DIRS = $(wildcard *)\n\ndefine newline\n\n\nendef\n\nall:\n\t  $(foreach dir, $(ALL_DIRS), -$(MAKE) -C./$(dir)/make_mc12101_nmpu1 run $(newline))\n')


def get_funcs_without_test(funcs_for_test, path_to_tests):
    funcs_with_test = [test_func + '\n' for test_func in os.listdir(path_to_tests)]
    return list(set(funcs_for_test) - set(funcs_with_test))


def get_funcs_without_perf_table(funcs_for_test, path_to_tables):
    funcs_with_table = [perf_table[:-2] for perf_table in os.listdir(path_to_tables)]
    return list(set(funcs_for_test) - set(funcs_with_table))


def generate_log(log_path, init_funcs, funcs_for_test, funcs_without_test, funcs_without_table):
    with open(os.path.join(log_path, "init_funcs.log"), 'a') as init_log:
        init_log.writelines(init_funcs)
    with open(os.path.join(log_path, "funcs_for_test.log"), 'a') as test_log:
        test_log.writelines(funcs_for_test)
    with open(os.path.join(log_path, "funcs_without_test.log"), 'a') as without_test_log:
        without_test_log.writelines(funcs_without_test)


cmd_args = parse_cmd_args()

log_dir_name = 'perf_test_log'
tests_dir_name = 'perf_tests'
tables_dir_name = 'perf_tables'
xml_dir_name = cmd_args.xml_dir_name

path_to_xml_dir = os.path.join(cmd_args.path_to_xml, cmd_args.xml_dir_name)
path_to_log_dir = os.path.join(cmd_args.path_to_log, log_dir_name)
path_to_tests_dir = os.path.join(cmd_args.path_to_tests, tests_dir_name)
path_to_tables_dir = os.path.join(cmd_args.path_to_tables, tables_dir_name)

xml_files = [file for file in os.listdir(path_to_xml_dir) if 'group__' in file]
try:
    os.mkdir(path_to_log_dir)
    os.mkdir(path_to_tests_dir)
    os.mkdir(path_to_tables_dir)
except OSError:
    pass
generate_makefile(path_to_tests_dir)
for file in xml_files:
    xml_obj = open_xml(os.path.join(path_to_xml_dir, file))
    try:
        perf_scripts = get_perf_scripts(xml_obj)
    except Exception as ex:
        print(file, ex)
        continue
    perf_scripts = parse_perf_scripts(perf_scripts)
    funcs_prototypes = get_funcs_prototypes(xml_obj)
    functions = parse_funcs_prototypes(funcs_prototypes)
    group_name = get_group_name(xml_obj)
    try:
        init_funcs, funcs_for_test = generate_perf_tests(functions, perf_scripts, 'mc12101', group_name, path_to_tests_dir)
    except Exception as err:
        print(err)
        continue
    funcs_without_test = get_funcs_without_test(funcs_for_test, path_to_tests_dir)
    funcs_without_table = get_funcs_without_perf_table(funcs_for_test, path_to_tables_dir)
    generate_log(path_to_log_dir, init_funcs, funcs_for_test, funcs_without_test, funcs_without_table)




# xml_obj = open_xml('group___m_t_r___copy.xml')
# perf_scripts = get_perf_scripts(xml_obj)
# perf_scripts = parse_perf_scripts(perf_scripts)
# funcs_prototypes = get_funcs_prototypes(xml_obj)
# functions = parse_funcs_prototypes(funcs_prototypes)
# group_name = get_group_name(xml_obj)
# generate_perf_tests(functions, perf_scripts, group_name)
