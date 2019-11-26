import os
import re
import random
import shutil

from collections import namedtuple

from tests_generator import xml_parser


def parse_perf_scripts(perf_scripts):
    prf_scs = []
    PerfScripts = namedtuple('PerfScripts', 'arguments_values arguments_names arguments_types size init deinit')
    for perf_script in perf_scripts:
        try:
            size = perf_script.pop(('custom_size_name_fig_podberesh', ''))
            size = size.strip()
        except Exception:
            size = None
        try:
            init_pos = list(perf_script.keys()).index(('init', ''))
            init_func = perf_script.pop(('init', ''))
            init_func = init_func.strip()
            init_func_pos = (init_func, init_pos)
        except Exception:
            init_func_pos = None
        try:
            deinit_func = perf_script.pop(('deinit', ''))
            deinit_func = deinit_func.strip()
        except Exception:
            deinit_func = None
        values_list = []
        types_list = []
        names_list = []
        for perf_param in perf_script.keys():
            param_value = perf_script.get(perf_param).strip()
            param_value = param_value.replace(' ', ', ')

            values_list.append(param_value)
            names_list.append(perf_param[0])
            types_list.append(perf_param[1])
        prf_scs.append(PerfScripts(values_list, names_list, types_list, size, init_func_pos, deinit_func))
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


def copy_build_for_board(path_to_build, path_to_test):
    if not os.path.exists(path_to_test):
        # shutil.rmtree(path_to_test)
        os.mkdir(path_to_test)
    for file in os.listdir(path_to_build):
        shutil.copy(os.path.join(path_to_build, file), path_to_test)
        shutil.copystat(os.path.join(path_to_build, file), path_to_test)


def get_contents_cppftest(path_to_build):
    build_dir_files = [f for f in os.listdir(path_to_build) if f[-4:] == '.cpp' or f[-2:] == '.c']
    if not build_dir_files:
        raise FileNotFoundError
    for file in build_dir_files:
        with open(os.path.join(path_to_build, file), 'r') as r_file:
            file_contents = r_file.readlines()
            for line in file_contents:
                if 'int main' in line:
                    return file, file_contents
    raise ValueError


def make_file_beginning(contents):
    file_beginning = ''.join(contents)
    num = file_beginning.find('return')
    return file_beginning[:num].rstrip()


def cast_args_for_init_func(perf_script, func):
    # Создние новой строки здесь необходимо, потому что в дальнейшем понадобится изменять perf_script.init (элемент кортежа),
    # который не может быть подвергнут изменению
    if perf_script.init is None:
        return ''
    init = '{0}'.format(perf_script.init[0])
    types = {'nm8s*': 'char*', 'nm16s*': 'short*', 'nm16s15b*': 'short*',
             'nm8u*': 'unsigned char*', 'nm16u*': 'unsigned short*'}
    for arg in re.findall(r'[$]\w+', perf_script.init[0]):
        try:
            nmpp_type_str = perf_script.param_types[perf_script.arguments_values.index(arg[1:])]
            if nmpp_type_str == '':
                nmpp_type_str = func.args_types[func.args_names.index(arg[1:])]
        except ValueError:
            nmpp_type_str = func.args_types[func.args_names.index(arg[1:])]
        type_str = types.get(nmpp_type_str)
        if type_str is None:
            type_str = nmpp_type_str
        init = init.replace(arg, '({0}){1}'.format(type_str, arg[1:]))
    return init


def write_code_to_cpptest(file_beginning, lists, cycles, names, printf, perf_scripts, group_name, size123, called_funcs, max_spaces, size_list, brackets, func, path_to_test):
    try:
        with open(path_to_test, 'w') as file:
            file.write(file_beginning)
            file.writelines(lists)
            file.writelines(names)
            file.write('\n  int t1, t2;')
            file.write('\n  float min, max;')
            file.write('\n  static char str[256];')
            file.write('\n  static char min_str[256];')
            file.write('\n  static char max_str[256];')
            file.write('\n  printf("{2}**{1}{3}ingroup {0}{1}{1}");'.format(group_name, r"\n", r"/", 3 * r"\tmp"[0]))
            for i, cycle in enumerate(cycles):
                file.write('\n  min = 1000000;')
                file.write('\n  max = 0;')
                s = '   |   '.join(perf_scripts[i].arguments_values)

                file.write('\n{\n')

                file.write('  printf("{1}Perfomance table {0}{1}{1}");\n'.format(str(i), r"\n"))
                file.write('  printf("{}   |   {:<13}  |  {}{}");\n'.format(s, 'ticks', 'ticks/elem', r"\n"))
                file.write('  printf("{}{}");\n\n'.format('---|---' * (len(perf_scripts[i].arguments_values) + 1), r"\n"))
                file.write(cycle)
                file.write(size123[i])
                file.write(called_funcs[i])
                file.write(printf[i])
                file.write('{0}printf(str);\n'.format(max_spaces[i]))
                file.write('{0}if(min > (float)(t2 -t1) / {2}) {1}\n'.format(max_spaces[i], r"{", size_list[i]))
                file.write('{0}  min = (float)(t2 - t1) / {1};\n'.format(max_spaces[i], size_list[i]))
                file.write('{0}  strcpy(min_str, str);\n'.format(max_spaces[i]))
                file.write('{0}{1}\n'.format(max_spaces[i], r"}"))

                file.write('{0}printf(str);\n'.format(max_spaces[i]))
                file.write('{0}if(max < (float)(t2 -t1) / {2}) {1}\n'.format(max_spaces[i], r"{", size_list[i]))
                file.write('{0}  max = (float)(t2 - t1) / {1};\n'.format(max_spaces[i], size_list[i]))
                file.write('{0}  strcpy(max_str, str);\n'.format(max_spaces[i]))
                file.write('{0}{1}\n'.format(max_spaces[i], r"}"))

                file.write(brackets[i])
                file.write('\n  printf("{0}The best configuration:{0}{0}");\n'.format(r"\n"))
                file.write('  printf("{}   |   {:<13}  |  {}{}");\n'.format(s, 'ticks', 'ticks/elem', r"\n"))
                file.write('  printf("{}{}");\n'.format('---|---' * (len(perf_scripts[i].arguments_values) + 1), r"\n"))
                file.write('\n  printf(min_str);\n')

                file.write('\n  printf("{0}The worst configuration:{0}{0}");\n'.format(r"\n"))
                file.write('  printf("{}   |   {:<13}  |  {}{}");\n'.format(s, 'ticks', 'ticks/elem', r"\n"))
                file.write('  printf("{}{}");\n'.format('---|---' * (len(perf_scripts[i].arguments_values) + 1), r"\n"))
                file.write('\n  printf(max_str);\n')

                file.write('}\n')

            file.write('\n')
            file.write('  printf("*/{}");\n'.format(r"\n"))
            file.write('  printf("{0}{1}{1}");\n'.format(func.prototype, r"\n"))
            file.write('  return 0;\n}\n')
        print('Creating the perf test for {}{}[OK]'.format(func.name, ' ' * (30 - len(func.name))))
        print('\n')
    except Exception as exc:
        print(path_to_test, exc)


def is_cpp_pointers(argument_values):
    if not argument_values.replace(', ', '').replace('.', '').replace('-', '').replace('0x', '').isdigit():
        return True
    return False


def get_type_from_func_prototype(func, argument_name):
    argument_name_in_func_prototype = func.args_names.index(argument_name)
    return func.args_types[argument_name_in_func_prototype]


def create_cycle_str(argument_type, argument_name, argument_values, argument_values_count, spaces,
                      index):
    if argument_values_count == 1:
        cycle_str = '{0}{1} {2} = ({1})({3});\n'.format(spaces, argument_type, argument_name,
                                                        argument_values)

    elif argument_values_count > 1:
        init_arg_str = '  {0}{1} = ({2})list{3}[i{3}];\n'.format(spaces,
                                                                 ' '.join([argument_type, argument_name]),
                                                                 argument_type, index)
        cycle_str = '{0}for(int i{1} = 0; i{1} < {2}; i{1}++) {3}{4}'.format(spaces, index,
                                                                             str(argument_values_count),
                                                                             '{\n', init_arg_str)
    return cycle_str


def create_names_str(index, argument_values_list):
    argument_values_in_quotes = ', '.join([''.join(['"', argument_value, '"']) for argument_value in argument_values_list])
    argument_values_in_brackets = ''.join(['{', argument_values_in_quotes, '}'])
    names_str = '\n  char* name{}[] = {};'.format(index, argument_values_in_brackets)
    return names_str


def create_lists_str(index, argument_values, argument_type):
    if is_cpp_pointers(argument_values):
        list_type = 'long long*'
    else:
        list_type = argument_type
    lists_str = '\n  {2} list{0}[] = {1};'.format(index, ''.join(['{', argument_values, '}']), list_type)
    return lists_str


def generate_perf_test_for_one_func(func, perf_scripts, group_name, test_name, file_beginning, point, path_to_build):
    print('Creating the perf test for {}...'.format(func.name))
    test_dir_name = '_'.join(['perf', func.name])  # Имя дериктории с тестом

    copy_build_for_board(path_to_build, test_dir_name)  # Копируем шаблон для будщего теста
    num = 0
    lists = []
    names = []
    cycles = []
    called_funcs = []
    max_spaces = []
    printf = []
    brackets = []
    size123 = []
    size_list = []
    path_to_test = os.path.join(test_dir_name, test_name)

    ''' В этом цикле перебираеются все сценарии производительности, описанные для группы(group_name) функций'''
    for perf_script in perf_scripts:
        called_str = '{}({};\n'.format(func.name, ', '.join(func.args_names))
        #init_args_str = ''
        printf_str = ''
        printf_args_str = ''
        names_str = ''
        lists_str = ''
        cycles_str = ''  # for the writting
        spaces = '  '  # строка с пробелами нужна для форматирования теста

        '''Если perf_script.init[1] == 0, значит функция инициализации должна стоять перед всеми циклами'''
        init = cast_args_for_init_func(perf_script, func)
        init_lst = init.split('\n')
        if perf_script.init is not None and perf_script.init[1] == 0:
            for s in init_lst:
                cycles_str += '  {0}\n'.format(s.strip())
        ''' В этом цикле перебирается все параметры сценария производительности'''
        for argument_values, argument_type, argument_name in zip(perf_script.arguments_values,
                                                                 perf_script.arguments_types,
                                                                 perf_script.arguments_names):
            # Если тип аргумента функции не был задан в сценарии производительности,
            # берем тип аргумента из прототипа функции
            if argument_type == '':
                argument_type = get_type_from_func_prototype(func, argument_name)

            index = str(num)
            argument_values_list = argument_values.split(', ')
            names_str += create_names_str(index, argument_values_list)
            '''Проверка на то, сколько значений для аргумента функции было задано в сценарии производительности.
               Если 1 параметр, то цикл не создается. (Если больше 1, то создается цикл.)
               Вместо него создается переменная, которой присваивается значение из сценария производительность.
               Эта переменная передается в качестве аргумента функции.'''
            argument_values_count = len(argument_values_list)
            if argument_values_count == 1:
                printf_args_str += 'name{0}[0], '.format(index)
            elif argument_values_count > 1:
                lists_str = create_lists_str(index, argument_values, argument_type)
                printf_args_str += 'name{0}[i{0}], '.format(index)
                spaces += '  '
            else:
                print("Error: {} hasn't values in this perf script!".format(argument_name))
            #cycles_str += '{0}{1}'.format(cycle_str, init_args_str)
            cycles_str += create_cycle_str(argument_type, argument_name, argument_values,
                                           argument_values_count, spaces, index)
            '''Проверяем, был ли указан в сценарии производительности (pss) тег init'''
            if perf_script.init is not None:
                '''Если тег init используется, то нужно проверить, есть ли в вызываемой функции инициализации параметры,
                   требующие приведения типов. Перед такими параметрами в вызове функции будет стоять знак $'''
                if perf_script.init[1] == num + 1:
                    for s in init_lst:
                        cycles_str += '{0}{1}\n'.format(spaces, s.strip())
            num += 1

        max_spaces.append(spaces)

        '''Проверяем, был ли указан в сценарии производительности (pss) тег size'''
        if perf_script.size is not None:
            size123_str = '{}int size123 = {};'.format(spaces, perf_script.size)
            size_str = 'size123'
        else:
            size123_str = ''
            size_str = ''.join(['atoi(', printf_args_str.split(', ')[-2], ')'])

        '''Проверяем, был ли указан в сценарии производительности (pss) тег deinit'''
        if perf_script.deinit is None:
            called_str = '{0}\n{0}t1 = clock();\n{0}{1});\n{0}t2 = clock();\n'.format(spaces, called_str[:-2])
        else:
            called_str = '{0}\n{0}t1 = clock();\n{0}{1});\n{0}t2 = clock();\n{0}{2}\n'.format(spaces, called_str[:-2],
                                                                                              perf_script.deinit)

        printf_str += '{:<13}'.format('%s |')
        printf_str += '{:<13}{}'.format('%d | ', '%0.2f')
        printf_str = ''.join(['"', printf_str, r'\n"'])
        sprintf_str = '{0}sprintf(str, {1}, {2} t2 - t1, (float)(t2 - t1) / {3});\n'.format(spaces, printf_str,
                                                                                             printf_args_str, size_str)
        lists.append(lists_str)
        cycles.append(cycles_str)
        called_funcs.append(called_str)
        names.append(names_str)
        printf.append(sprintf_str)
        size123.append(size123_str)
        size_list.append(size_str)
        count_cycles = cycles_str.count('for(int ')
        brackets_str = ''
        for i in range(count_cycles):
            spaces = spaces.replace('  ', '', 1)
            brackets_str += spaces + '}\n'
        brackets.append(brackets_str)
    write_code_to_cpptest(file_beginning, lists, cycles, names, printf, perf_scripts, group_name, size123, called_funcs, max_spaces, size_list, brackets, func, path_to_test)


def generate_perf_tests_from_one_xml(functions, perf_scripts, group_name, test_name, file_beginning, point, path_to_build):
    init_funcs = []
    funcs_for_test = []

    '''В этом цикле перебируется все функции, найденные в одном
       xml-файле (в одном файле функции, относящиеся к одной группе group_name)'''
    for func in functions:
        # Проверяем для какой точки (плавающей или фиксированной) попалась функция и сопостовляем с ключом -p
        if point == 'fixed':
            if is_float_func(func):
                continue
        if point == 'float':
            if not is_float_func(func):
                continue

        '''Проверяем, совпадают ли аргументы тестируемой функции с аргументами,
           указаныыми в сценарии производительности, для этой функции.
           Если не совпадают, то такая функция пропускается, тест для нее не создается'''
        if set(func.args_names) != set(perf_scripts[0].arguments_names):
            init_funcs.append(func.name + '\n')
            print('-----------------------------------------------------')
            print('Warning:')
            print('{} args = {} mismatch with the testperf args = {}.'.format(func.name, func.args_names, perf_scripts[0].arguments_values))
            print('-----------------------------------------------------')
        else:
            funcs_for_test.append(func.name + '\n')

        generate_perf_test_for_one_func(func, perf_scripts, group_name, test_name, file_beginning, point, path_to_build)

    return init_funcs, funcs_for_test


def generate_perf_tests_from_all_xml(cmd_args):
    abs_path_to_build = os.path.abspath(cmd_args.path_to_build)
    abs_path_to_xml = os.path.abspath(cmd_args.path_to_xml)

    if not os.path.exists(abs_path_to_build):
        print('-----------------------------------------------------')
        print("Error! Path: '{}' doesn't exist".format(cmd_args.path_to_build))
        print("The perf tests won't be created!")
        print('-----------------------------------------------------')
        return

    try:
        test_name, perf_test_contents = get_contents_cppftest(abs_path_to_build)
    except FileNotFoundError:
        print('-------------------------------------------------------')
        print('Error:')
        print("A template with a 'int main()' function wasn't found!")
        print("The perf tests won't be created!")
        print('-------------------------------------------------------')
        return
    except ValueError:
        print('-------------------------------------------------------')
        print('Error:')
        print("'int main()' function wasn't found in the template!")
        print("The perf tests won't be created!")
        print('-------------------------------------------------------')
        return

    file_beginning = make_file_beginning(perf_test_contents)

    xml_files = [file for file in os.listdir(abs_path_to_xml) if 'group__' in file]
    if not xml_files:
        print('-------------------------------------------------------')
        print("xml files with the functions prototypes weren't found!")
        print("The perf tests won't be created!")
        print('-------------------------------------------------------')
        return

    for file in xml_files:
        try:
            xml_obj = xml_parser.open_xml(os.path.join(abs_path_to_xml, file))
            perf_scripts = xml_parser.get_perf_scripts(xml_obj)
        except SyntaxError:
            print('Error!\n' + file + ': a syntax error in the perf script')
            continue
        except Exception as ex:
            print(file, ex)
            continue
        perf_scripts = parse_perf_scripts(perf_scripts)
        funcs_prototypes = xml_parser.get_funcs_prototypes(xml_obj)
        functions = parse_funcs_prototypes(funcs_prototypes)
        group_name = xml_parser.get_group_name(xml_obj)
        try:
            generate_perf_tests_from_one_xml(functions, perf_scripts, group_name, test_name,
                                             file_beginning, cmd_args.point, abs_path_to_build)
        except Exception as err:
            print(err)
            continue
