import os
import re
import random
import shutil

from collections import namedtuple

from tests_generator import xml_parser


def is_float_func(func):
    for arg_type in func.args_types:
        if arg_type.find('f') != -1 or arg_type.find('double') != -1:
            return True
    return False


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


def write_code_to_cpptest(file_beginning, lists, cycles, names, printf, perf_scripts, group_name, sizes_tags, called_funcs, max_spaces, sizes_sprintf, brackets, func, path_to_test):
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
                file.write(sizes_tags[i])
                file.write(called_funcs[i])
                file.write(printf[i])
                file.write('{0}printf(str);\n'.format(max_spaces[i]))
                file.write('{0}if(min > (float)(t2 -t1) / {2}) {1}\n'.format(max_spaces[i], r"{", sizes_sprintf[i]))
                file.write('{0}  min = (float)(t2 - t1) / {1};\n'.format(max_spaces[i], sizes_sprintf[i]))
                file.write('{0}  strcpy(min_str, str);\n'.format(max_spaces[i]))
                file.write('{0}{1}\n'.format(max_spaces[i], r"}"))

                file.write('{0}printf(str);\n'.format(max_spaces[i]))
                file.write('{0}if(max < (float)(t2 -t1) / {2}) {1}\n'.format(max_spaces[i], r"{", sizes_sprintf[i]))
                file.write('{0}  max = (float)(t2 - t1) / {1};\n'.format(max_spaces[i], sizes_sprintf[i]))
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




def generate_perf_test_for_one_func(func, perf_scripts, group_name, test_name, file_beginning, point, path_to_build):
    print('Creating the perf test for {}...'.format(func.name))
    test_dir_name = '_'.join(['perf', func.name])  # Имя дериктории с тестом

    copy_build_for_board(path_to_build, test_dir_name)  # Копируем шаблон для будщего теста
    num = 0
    lists = []
    names = []
    cycles = []
    funcs_calls = []
    max_spaces = []
    printf = []
    brackets = []
    sizes_tags = []
    sizes_sprintf = []
    path_to_test = os.path.join(test_dir_name, test_name)

    ''' В этом цикле перебираеются все сценарии производительности, описанные для группы(group_name) функций'''
    for perf_script in perf_scripts:
        #init_args_str = ''
        printf_str = ''
        names_for_sprintf_str = ''
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
            cycles_str += create_cycle_str(argument_type, argument_name, argument_values,
                                           argument_values_count, spaces, index)
            if argument_values_count == 1:
                names_for_sprintf_str += 'name{0}[0], '.format(index)
            elif argument_values_count > 1:
                lists_str = create_lists_str(index, argument_values, argument_type)
                names_for_sprintf_str += 'name{0}[i{0}], '.format(index)
                spaces += '  '
            else:
                print("Error: {} hasn't values in this perf script!".format(argument_name))
            #cycles_str += '{0}{1}'.format(cycle_str, init_args_str)
            '''Проверяем, был ли указан в сценарии производительности (pss) тег init'''
            if perf_script.init is not None:
                '''Если тег init используется, то нужно проверить, есть ли в вызываемой функции инициализации параметры,
                   требующие приведения типов. Перед такими параметрами в вызове функции будет стоять знак $'''
                if perf_script.init[1] == num + 1:
                    for s in init_lst:
                        cycles_str += '{0}{1}\n'.format(spaces, s.strip())
            num += 1

        max_spaces.append(spaces)

        size_tag_str = create_size_tag_str(spaces, perf_script)
        size_sprintf_str = create_size_sprintf_str(names_for_sprintf_str, perf_script)

        func_call_str = create_func_call_str(spaces, func, perf_script)
        sprintf_str = create_sprintf_str(spaces, names_for_sprintf_str, size_sprintf_str)

        lists.append(lists_str)
        cycles.append(cycles_str)
        funcs_calls.append(func_call_str)
        names.append(names_str)
        printf.append(sprintf_str)
        sizes_tags.append(size_tag_str)
        sizes_sprintf.append(size_sprintf_str)
        count_cycles = cycles_str.count('for(int ')
        brackets_str = ''
        for i in range(count_cycles):
            spaces = spaces.replace('  ', '', 1)
            brackets_str += spaces + '}\n'
        brackets.append(brackets_str)
    write_code_to_cpptest(file_beginning, lists, cycles, names, printf, perf_scripts, group_name, sizes_tags, funcs_calls, max_spaces, sizes_sprintf, brackets, func, path_to_test)


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

        test_dir_name = '_'.join(['perf', func.name])  # Имя дериктории с тестом

        copy_build_for_board(path_to_build, test_dir_name)  # Копируем шаблон для будщего теста

        path_to_test = os.path.join(test_dir_name, test_name)

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
        test_name, perf_test_contents = get_contents_cpptest(abs_path_to_build)
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
