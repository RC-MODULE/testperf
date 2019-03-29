import os
import re
import random
import shutil

from collections import namedtuple

from tests_generator import xml_parser
from tests_generator import logs_generator


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


# def create_make_dir_name(board, point):
#     make_dir_name = '_'.join(['make', board])
#     if board == 'mc12101':
#         nmpu = ''
#         if point == 'float':
#             nmpu = '_nmpu0'
#         else:
#             nmpu = '_nmpu1'
#         make_dir_name += nmpu
#     return make_dir_name


def copy_build_for_board(path_to_build, path_to_test):
    try:
        shutil.copytree(path_to_build, path_to_test)
    except OSError as error:
        raise error


def get_contents_cppftest(path_to_build):
    build_dir_files = os.listdir(path_to_build)
    for file in build_dir_files:
        with open(os.path.join(path_to_build, file), 'r') as r_file:
            file_contents = r_file.readlines()
            for line in file_contents:
                if 'int main' in line:
                    return file, file_contents


def make_file_beginning(contents):
    file_beginning = ''.join(contents)
    num = file_beginning.find('return')
    return file_beginning[:num]


def generate_perf_tests_from_one_xml(functions, perf_scripts, group_name, test_name, file_beginning, point, path_to_build):
    init_funcs = []
    funcs_for_test = []
    for func in functions:
        if point == 'fixed':
            if is_float_func(func):
                continue
        if point == 'float':
            if not is_float_func(func):
                continue
        if set(func.args_names) != set(perf_scripts[0].args_names):
            init_funcs.append(func.name + '\n')
            continue
        else:
            funcs_for_test.append(func.name + '\n')
        test_dir_name = '_'.join(['perf', func.name])
        copy_build_for_board(path_to_build, test_dir_name)
        num = 0
        lists = []    # for the writting
        names = []
        cycles = []  # for the writting
        called_funcs = []
        init_args = []
        print_f = []
        path_to_test = os.path.join(test_dir_name, test_name)
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
                file.write('\n  clock_t t1, t2;\n')
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


def generate_makefile(point):
    make_dir_name = 'make_mc12101_nmc0'
    with open("Makefile", 'w') as file:
        file.write('ALL_DIRS = $(wildcard *)\n\ndefine newline\n\n\nendef\n\nall:\n\t  $(foreach dir, $(ALL_DIRS), -$(MAKE) -C./$(dir)/{} run $(newline))\n'.format(make_dir_name))


def generate_perf_tests_from_all_xml(cmd_args):
    log_dir_name = 'perf_test_log_{}'.format(cmd_args.point)
    #tests_dir_name = 'perf_tests_{}'.format(cmd_args.point)
    tables_dir_name = 'perf_tables_{}'.format(cmd_args.point)

    path_to_log_dir = os.path.join(cmd_args.path_to_log, log_dir_name)
    #path_to_tests_dir = os.path.join(cmd_args.path_to_tests, tests_dir_name)
    #path_to_tables_dir = os.path.join(cmd_args.path_to_tables, tables_dir_name)

    test_name, perf_test_contents = get_contents_cppftest(cmd_args.path_to_build)
    file_beginning = make_file_beginning(perf_test_contents)

    xml_files = [file for file in os.listdir(cmd_args.path_to_xml) if 'group__' in file]
    try:
        os.mkdir(path_to_log_dir)
        #os.mkdir(path_to_tests_dir)
        #os.mkdir(path_to_tables_dir)
    except OSError:
        pass
    #generate_makefile(cmd_args.point)
    for file in xml_files:
        xml_obj = xml_parser.open_xml(os.path.join(cmd_args.path_to_xml, file))
        # print(file)
        try:
            perf_scripts = xml_parser.get_perf_scripts(xml_obj)
        except Exception as ex:
            print(file, ex)
            continue
        perf_scripts = parse_perf_scripts(perf_scripts)
        funcs_prototypes = xml_parser.get_funcs_prototypes(xml_obj)
        functions = parse_funcs_prototypes(funcs_prototypes)
        group_name = xml_parser.get_group_name(xml_obj)
        try:
            init_funcs, funcs_for_test = generate_perf_tests_from_one_xml(functions,
                                                                          perf_scripts,
                                                                          group_name,
                                                                          test_name,
                                                                          file_beginning,
                                                                          cmd_args.point,
                                                                          cmd_args.path_to_build)
        except Exception as err:
            print(err)
            continue
        #funcs_without_test = get_funcs_without_test(funcs_for_test, path_to_tests_dir)
        #funcs_without_table = logs_generator.get_funcs_without_perf_table(funcs_for_test, path_to_tables_dir)
        #logs_generator.generate_log(path_to_log_dir, init_funcs, funcs_for_test, funcs_without_table)
