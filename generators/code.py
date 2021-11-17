#######################################################
# Software designer: A.Brodyazhenko
# Year: 2019
# Content: Class for generating a cpp code for perf test
#######################################################

import re
from collections import namedtuple


class CpptestCodeGenerator:
    def __init__(self, func, perf_scripts):
        self.__function = func
        self.__perf_scripts = perf_scripts
        self.__cpptest_code = namedtuple('CpptestCode', ['lists', 'names', 'cycles',
                                                         'funcs_calls', 'max_spaces',
                                                         'printf', 'brackets', 'sizes_tags', 'sizes_sprintf'])

        self.__cpptest_code.lists = []
        self.__cpptest_code.names = []
        self.__cpptest_code.cycles = []
        self.__cpptest_code.funcs_calls = []
        self.__cpptest_code.max_spaces = []
        self.__cpptest_code.printf = []
        self.__cpptest_code.brackets = []
        self.__cpptest_code.sizes_tags = []
        self.__cpptest_code.sizes_sprintf = []

        self.__vars_num_in_cpptest = 0

    def generate_cpptest_code(self):
        print('Creating the perf test for {}...'.format(self.__function.name))
        ''' В этом цикле перебираеются все сценарии производительности, описанные для группы(group_name) функций'''
        for perf_script in self.__perf_scripts:
            argument_for_sprintf = ''
            names_for_sprintf_str = ''
            names_str = ''
            lists_str = ''
            cycles_str = ''
            spaces = '  '  # строка с пробелами нужна для форматирования теста

            '''Если perf_script.initialization_func[1] == 0, значит функция
               инициализации должна стоять перед всеми циклами'''
            init = self.cast_args_for_init_func(perf_script)
            init_lst = init.split('\n')
            if perf_script.initialization_func is not None and perf_script.initialization_func[1] == 0:
                for s in init_lst:
                    cycles_str += '  {0}\n'.format(s.strip())
            ''' В этом цикле перебирается все параметры сценария производительности'''
            argument_local_index=0
            for argument_values, argument_type, argument_name in zip(perf_script.arguments_values,
                                                                     perf_script.arguments_types,
                                                                     perf_script.arguments_names):
                # Если тип аргумента функции не был задан в сценарии производительности,
                # берем тип аргумента из прототипа функции
                if argument_type == '':
                    argument_type = self.fetch_type_from_func_prototype(argument_name)

                index = str(self.__vars_num_in_cpptest)
                argument_values_list = argument_values.split(', ')
                argument_for_sprintf += '{:<13}'.format('%s |')
                names_str += self.create_names_str(index, argument_values_list)
                '''Проверка на то, сколько значений для аргумента функции было задано в сценарии производительности.
                   Если 1 параметр, то цикл не создается. (Если больше 1, то создается цикл.)
                   Вместо него создается переменная, которой присваивается значение из сценария производительность.
                   Эта переменная передается в качестве аргумента функции.'''
                argument_values_count = len(argument_values_list)
                cycles_str += self.create_cycle_str(argument_type, argument_name, argument_values,
                                                    argument_values_count, spaces, index)
                if argument_values_count == 1:
                    names_for_sprintf_str += 'name{0}[0], '.format(index)
                elif argument_values_count > 1:
                    lists_str += self.create_lists_str(index, argument_values, argument_type)
                    names_for_sprintf_str += 'name{0}[i{0}], '.format(index)
                    spaces += '  '
                else:
                    print("Error: {} hasn't values in this perf script!".format(argument_name))
                '''Проверяем, был ли указан в сценарии производительности (perf_script) тег init'''
                if perf_script.initialization_func is not None:
                    '''Если тег init используется, то нужно проверить, есть ли в вызываемой функции инициализации параметры,
                       требующие приведения типов. Перед такими параметрами в вызове функции будет стоять знак $'''
                    #if perf_script.initialization_func[1] == self.__vars_num_in_cpptest + 1:
                    if perf_script.initialization_func[1] == argument_local_index + 1:
                        for s in init_lst:
                            cycles_str += '{0}{1}\n'.format(spaces, s.strip())
                self.__vars_num_in_cpptest += 1
                argument_local_index +=1 # счетчик индекса переменной внутри сценария

            self.__cpptest_code.max_spaces.append(spaces)

            size_tag_str = self.create_size_tag_str(spaces, perf_script)
            size_sprintf_str = self.create_size_sprintf_str(names_for_sprintf_str, perf_script)

            func_call_str = self.create_func_call_str(spaces, self.__function, perf_script)
            sprintf_str = self.create_sprintf_str(spaces, names_for_sprintf_str, size_sprintf_str, argument_for_sprintf)

            self.__cpptest_code.lists.append(lists_str)
            self.__cpptest_code.cycles.append(cycles_str)
            self.__cpptest_code.funcs_calls.append(func_call_str)
            self.__cpptest_code.names.append(names_str)
            self.__cpptest_code.printf.append(sprintf_str)
            self.__cpptest_code.sizes_tags.append(size_tag_str)
            self.__cpptest_code.sizes_sprintf.append(size_sprintf_str)
            count_cycles = cycles_str.count('for(int ')
            brackets_str = ''
            for i in range(count_cycles):
                spaces = spaces.replace('  ', '', 1)
                brackets_str += spaces + '}\n'
            self.__cpptest_code.brackets.append(brackets_str)

    def get_cpptest_code(self):
        return self.__cpptest_code

    def fetch_type_from_func_prototype(self, argument_name):
        index = self.__function.arguments_names.index(argument_name)
        return self.__function.arguments_types[index]

    def create_lists_str(self, index, argument_values, argument_type):
        if self.is_cpp_pointers(argument_values):
            list_type = 'long long*'
        else:
            list_type = argument_type
        lists_str = '\n  {2} list{0}[] = {1};'.format(index, ''.join(['{', argument_values, '}']), list_type)
        return lists_str

    def cast_args_for_init_func(self, perf_script):
        # Создние новой строки здесь необходимо, потому что в дальнейшем понадобится изменять
        # perf_script.init (элемент кортежа), который не может быть подвергнут изменению
        if perf_script.initialization_func is None:
            return ''
        init = '{0}'.format(perf_script.initialization_func[0])
        types = {'nm8s*': 'char*', 'nm16s*': 'short*', 'nm16s15b*': 'short*',
                 'nm8u*': 'unsigned char*', 'nm16u*': 'unsigned short*'}
        for arg in re.findall(r'[$]\w+', perf_script.initialization_func[0]):
            try:
                nmpp_type_str = perf_script.arguments_types[perf_script.arguments_values.index(arg[1:])]
                if nmpp_type_str == '':
                    nmpp_type_str = self.__function.arguments_types[self.__function.arguments_names.index(arg[1:])]
            except ValueError:
                nmpp_type_str = self.__function.arguments_types[self.__function.arguments_names.index(arg[1:])]
            type_str = types.get(nmpp_type_str)
            if type_str is None:
                type_str = nmpp_type_str
            init = init.replace(arg, '({0}){1}'.format(type_str, arg[1:]))
        return init

    @staticmethod
    def create_cycle_str(argument_type, argument_name, argument_values, argument_values_count, spaces, index):
        cycle_str = ''
        if argument_values_count == 1:
            cycle_str = '{0}{1} {2} = ({1})({3});\n'.format(spaces, argument_type, argument_name, argument_values)

        elif argument_values_count > 1:
            init_arg_str = '  {0}{1} = ({2})list{3}[i{3}];\n'.format(spaces,
                                                                     ' '.join([argument_type, argument_name]),
                                                                     argument_type, index)
            cycle_str = '{0}for(int i{1} = 0; i{1} < {2}; i{1}++) {3}{4}'.format(spaces, index,
                                                                                 str(argument_values_count),
                                                                                 '{\n', init_arg_str)
        return cycle_str

    @staticmethod
    def is_cpp_pointers(argument_values):
        if not argument_values.replace(', ', '').replace('.', '').replace('-', '').replace('0x', '').isdigit():
            return True
        return False

    @staticmethod
    def create_names_str(index, argument_values_list):
        argument_values_in_quotes = ', '.join([''.join(['"', argument_value, '"']) for argument_value in argument_values_list])
        argument_values_in_brackets = ''.join(['{', argument_values_in_quotes, '}'])
        names_str = '\n  const char* name{}[] = {};'.format(index, argument_values_in_brackets)
        return names_str

    @staticmethod
    def create_func_call_str(spaces, func, perf_script):
        func_call_str = '{}({};\n'.format(func.name, ', '.join(func.arguments_names))
        '''Проверяем, был ли указан в сценарии производительности (pss) тег deinit'''
        if perf_script.deinitialization_func is None:
            func_call_str = '{0}\n{0}t1 = clock();\n{0}{1});\n{0}t2 = clock();\n'.format(spaces, func_call_str[:-2])
        else:
            func_call_str = '{0}\n{0}t1 = clock();\n{0}{1});\n{0}t2 = clock();\n{0}{2}\n'.format(spaces,
                                                                                                 func_call_str[:-2],
                                                                                                 perf_script.deinitialization_func)
        return func_call_str

    @staticmethod
    def create_size_tag_str(spaces, perf_script):
        size_tag_str = ''
        '''Если тег не задан, то считаем, что size передается как последний аргумент функции'''
        if perf_script.size is not None:
            size_tag_str += '{}int size_tag = {};'.format(spaces, perf_script.size)
        return size_tag_str

    @staticmethod
    def create_size_sprintf_str(names_for_sprintf_str, perf_script):
        size_sprintf_str = ''
        '''Если тег не задан, то берем значение последнего аргумента функции'''
        if perf_script.size is not None:
            size_sprintf_str += 'size_tag'
        else:
            size_sprintf_str += ''.join(['atoi(', names_for_sprintf_str.split(', ')[-2], ')'])
        return size_sprintf_str

    @staticmethod
    def create_sprintf_str(spaces, names_for_sprintf_str, size_sprintf_str, argument_for_sprintf):
        argument_for_sprintf += '{:<13}{}'.format('%d | ', '%0.2f')
        argument_for_sprintf_in_quotes = ''.join(['"', argument_for_sprintf, r'\n"'])
        sprintf_str = '{0}sprintf(str, {1}, {2} t2 - t1, (float)(t2 - t1) / {3});\n'.format(spaces,
                                                                                            argument_for_sprintf_in_quotes,
                                                                                            names_for_sprintf_str,
                                                                                            size_sprintf_str)
        return sprintf_str

if __name__ == '__main__':
    pass
