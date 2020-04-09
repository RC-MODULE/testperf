#######################################################
# Software designer: A.Brodyazhenko
# Year: 2019
# Content: Class for generating perf tests
#######################################################

import os
from doxy.parsers.testperf_tag import TestperfTagParser
from doxy.parsers.memberdef_tag import MemberdefTagParser
from doxy.parsers.xml import DoxyXmlParser
from generators.build_template import BuildTemplateGenerator
from generators.code import CpptestCodeGenerator


class CpptestsGenerator:
    def __init__(self, path_to_build_template, path_to_doxy_xml, point_type):
        self.__abspath_to_build = os.path.abspath(path_to_build_template)
        self.__abspath_to_doxy_xml = os.path.abspath(path_to_doxy_xml)
        self.__path_to_build_template = path_to_build_template
        self.__point_type = point_type
        self.__build_template_gen = BuildTemplateGenerator(path_to_build_template)

        try:
            self.__cpptest_beginning = self.__build_template_gen.generate_cpptest_beginning()
        except FileNotFoundError:
            print('-------------------------------------------------------')
            print('Error:')
            print("A template with a 'int main()' function wasn't found!")
            print("The cpptests won't be created!")
            print('-------------------------------------------------------')
            return
        except ValueError:
            print('-------------------------------------------------------')
            print('Error:')
            print("'int main()' function wasn't found in the template!")
            print("The cpptests won't be created!")
            print('-------------------------------------------------------')
            return

    def generate_cpptests_from_some_doxy_xml(self):
        if not os.path.exists(self.__abspath_to_build):
            print('-----------------------------------------------------')
            print("Error! Path: '{}' doesn't exist".format(self.__abspath_to_build))
            print("The perf tests won't be created!")
            print('-----------------------------------------------------')
            return

        doxy_xml_names = [file_name for file_name in os.listdir(self.__abspath_to_doxy_xml) if 'group__' in file_name]
        if not doxy_xml_names:
            print('-------------------------------------------------------')
            print("Doxy xml files with the functions prototypes weren't found!")
            print("The perf cpptests won't be created!")
            print('-------------------------------------------------------')
            return

        doxy_xml_names_without_testperf_tag = []
        for doxy_xml_name in doxy_xml_names:
            try:
                doxy_xml_parser = DoxyXmlParser(os.path.join(self.__abspath_to_doxy_xml, doxy_xml_name))
            except SyntaxError:
                print('Error!\n' + doxy_xml_name + ': a syntax error in the perf script')
                continue

            testperf_tags = doxy_xml_parser.get_testperf_tags()
            if testperf_tags:
                perf_scripts = []
                for testperf_tag in testperf_tags:
                    testperf_tag_parser = TestperfTagParser(testperf_tag)
                    testperf_tag_parser.parse_testperf_tag()
                    perf_scripts.append(testperf_tag_parser.get_perf_script())

                memberdef_tags = doxy_xml_parser.get_memberdef_tags()
                functions = []
                for memberdef_tag in memberdef_tags:
                    memberdef_tag_parser = MemberdefTagParser(memberdef_tag)
                    memberdef_tag_parser.parse_memberdef_tag()
                    functions.append(memberdef_tag_parser.get_function())

                compoundname = doxy_xml_parser.get_compoundname_tag()

                try:
                    self.generate_cpptests_from_one_doxy_xml(functions, perf_scripts, compoundname)
                except Exception as err:
                    print(err)
                    continue
            else:
                doxy_xml_names_without_testperf_tag.append(doxy_xml_name)
                continue

        if doxy_xml_names_without_testperf_tag:
            print("These doxy xml doesn't have testperf tag.")
            print("For functions from these doxy xml cpp tests were not created:")
            for doxy_xml_name_without_testperf_tag in doxy_xml_names_without_testperf_tag:
                print(doxy_xml_name_without_testperf_tag)

    def generate_cpptests_from_one_doxy_xml(self, functions, perf_scripts, compoundname):
        # В этом цикле перебируется все функции, найденные в одном
        # doxy xml-файле (в одном файле функции, относящиеся к одной группе group_name)'''
        for func in functions:
            # Проверяем для какой точки (плавающей или фиксированной) попалась функция и сопостовляем с ключом -p
            if self.__point_type == 'fixed':
                if func.point_type == 'floating':
                    continue
            if self.__point_type == 'floating':
                if func.point_type == 'fixed':
                    continue

            '''Проверяем, совпадают ли аргументы тестируемой функции с аргументами,
               указаныыми в сценарии производительности, для этой функции.
               Если не совпадают, то выводится предупреждение, cpp тест производительности все равно создается'''
            if set(func.arguments_names) != set(perf_scripts[0].arguments_names):
                #init_funcs.append(func.name + '\n')
                print('-----------------------------------------------------')
                print('Warning:')
                print('{} args = {} mismatch with the testperf args = {}.'.format(func.name, func.arguments_names,
                                                                                  perf_scripts[0].arguments_names))
                print('-----------------------------------------------------')

            cpptest_code_generator = CpptestCodeGenerator(func, perf_scripts)
            cpptest_code_generator.generate_cpptest_code()
            cpptest_code = cpptest_code_generator.get_cpptest_code()

            cpptest_dir_name = '_'.join(['perf', func.name])  # Имя дериктории с тестом
            self.__build_template_gen.copy(cpptest_dir_name)  # Копируем шаблон для будщего теста

            path_to_cpptest = os.path.join(cpptest_dir_name, self.__build_template_gen.get_cpptest_template_name())

            self.write_code_to_cpptest(cpptest_code, perf_scripts, func, compoundname, path_to_cpptest)

    def write_code_to_cpptest(self, cpptest_code, perf_scripts, func, compoundname, path_to_cpptest):
        try:
            with open(path_to_cpptest, 'w') as file:
                file.write(self.__cpptest_beginning)
                file.writelines(cpptest_code.lists)
                file.writelines(cpptest_code.names)
                file.write('\n  int t1, t2;')
                file.write('\n  float min, max;')
                file.write('\n  static char str[256];')
                file.write('\n  static char min_str[256];')
                file.write('\n  static char max_str[256];')
                file.write(
                    '\n  printf("{2}**{1}{3}ingroup {0}{1}{1}");'.format(compoundname, r"\n", r"/", 3 * r"\tmp"[0]))
                for i, cycle in enumerate(cpptest_code.cycles):
                    file.write('\n  min = 1000000;')
                    file.write('\n  max = 0;')
                    s = '   |   '.join(perf_scripts[i].arguments_names)

                    file.write('\n{\n')

                    file.write('  printf("{1}Perfomance table {0}{1}{1}");\n'.format(str(i), r"\n"))
                    file.write('  printf("{}   |   {:<13}  |  {}{}");\n'.format(s, 'ticks', 'ticks/elem', r"\n"))
                    file.write(
                        '  printf("{}{}");\n\n'.format('---|---' * (len(perf_scripts[i].arguments_names) + 1), r"\n"))
                    file.write(cycle)
                    file.write(cpptest_code.sizes_tags[i])
                    file.write(cpptest_code.funcs_calls[i])
                    file.write(cpptest_code.printf[i])
                    file.write('{0}printf(str);\n'.format(cpptest_code.max_spaces[i]))
                    file.write('{0}if(min > (float)(t2 -t1) / {2}) {1}\n'.format(cpptest_code.max_spaces[i], r"{", cpptest_code.sizes_sprintf[i]))
                    file.write('{0}  min = (float)(t2 - t1) / {1};\n'.format(cpptest_code.max_spaces[i], cpptest_code.sizes_sprintf[i]))
                    file.write('{0}  strcpy(min_str, str);\n'.format(cpptest_code.max_spaces[i]))
                    file.write('{0}{1}\n'.format(cpptest_code.max_spaces[i], r"}"))

                    file.write('{0}printf(str);\n'.format(cpptest_code.max_spaces[i]))
                    file.write('{0}if(max < (float)(t2 -t1) / {2}) {1}\n'.format(cpptest_code.max_spaces[i], r"{", cpptest_code.sizes_sprintf[i]))
                    file.write('{0}  max = (float)(t2 - t1) / {1};\n'.format(cpptest_code.max_spaces[i], cpptest_code.sizes_sprintf[i]))
                    file.write('{0}  strcpy(max_str, str);\n'.format(cpptest_code.max_spaces[i]))
                    file.write('{0}{1}\n'.format(cpptest_code.max_spaces[i], r"}"))

                    file.write(cpptest_code.brackets[i])
                    file.write('\n  printf("{0}The best configuration:{0}{0}");\n'.format(r"\n"))
                    file.write('  printf("{}   |   {:<13}  |  {}{}");\n'.format(s, 'ticks', 'ticks/elem', r"\n"))
                    file.write(
                        '  printf("{}{}");\n'.format('---|---' * (len(perf_scripts[i].arguments_names) + 1), r"\n"))
                    file.write('\n  printf(min_str);\n')

                    file.write('\n  printf("{0}The worst configuration:{0}{0}");\n'.format(r"\n"))
                    file.write('  printf("{}   |   {:<13}  |  {}{}");\n'.format(s, 'ticks', 'ticks/elem', r"\n"))
                    file.write(
                        '  printf("{}{}");\n'.format('---|---' * (len(perf_scripts[i].arguments_names) + 1), r"\n"))
                    file.write('\n  printf(max_str);\n')

                    file.write('}\n')

                file.write('\n')
                file.write('  printf("*/{}");\n'.format(r"\n"))
                file.write('  printf("{0}{1}{1}");\n'.format(func.prototype, r"\n"))
                file.write('  return 0;\n}\n')
            print('Creating the perf test for {}{}[OK]'.format(func.name, ' ' * (30 - len(func.name))))
            print('\n')
        except Exception as exc:
            print(path_to_cpptest, exc)

if __name__ == '__main__':
    pass
