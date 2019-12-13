
import sys
import argparse

from testperf_manager import *


main_parser = argparse.ArgumentParser()
main_parser.add_argument('--path_to_tests', default='.', help='Path following which'
                                                              ' the generator will make perf tests')
main_parser.add_argument('--path_to_doxy_xml', default=os.path.join('doxy', 'xml'), help='Path following which the '
                                                                                         ' generator will find xml'
                                                                                         ' after doxygen work')
main_parser.add_argument('--path_to_log', default='.', help='Path following which the generator will make logs')

subparsers = main_parser.add_subparsers()

config_parser = subparsers.add_parser('config')
config_parser.add_argument('-i', '--path_to_headers', required=True, help='Path to include dir')
config_parser.add_argument('-b', '--path_to_build', required=True, help='Path to build dir')

# Если ключ -p не задан, то тесты будут сгенерированы для всех типов точек по уполчанию
# Если ключ -p задан, например, floating, то тесты сгенерятся только для функций,
# принимающих хотя бы один аргумент с плавающей точкой, остальные функции будут пропущены
config_parser.add_argument('-p', '--point_type', default='all', help=('It can take a value = all (all types)'
                                                                      ' value = floating',
                                                                      '(perf tests for floating point)',
                                                                      ' or fixed(perf tests for fixed)'))

config_parser.set_defaults(func=configure_cpptests)
run_parser = subparsers.add_parser('run')
run_parser.set_defaults(func=run_cpptests)

del_parser = subparsers.add_parser('del')
del_parser.set_defaults(func=delete_cpptests)

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

parsed_cmd_keys = main_parser.parse_args(sys.argv[1:])
parsed_cmd_keys.func(parsed_cmd_keys)

