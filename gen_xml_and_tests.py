
import os
import sys
import argparse

from doxy import doxy
from tests_generator import perf_tests_generator


def parse_cmd_args():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('-p', '--point', default='float')
    args_parser.add_argument('--path_to_build')
    args_parser.add_argument('--path_to_inc')
    args_parser.add_argument('--path_to_xml', default=os.path.join('doxy', 'xml'))
    args_parser.add_argument('--path_to_tests', default='.')
    #args_parser.add_argument('--path_to_tables', default='.')
    args_parser.add_argument('--path_to_log', default='.')
    args_parser.add_argument('--xml_dir_name', default='xml')

    console_args = args_parser.parse_args(sys.argv[1:])

    return console_args

parsed_cmd_args = parse_cmd_args()

doxy.make_xml(parsed_cmd_args.path_to_inc)
perf_tests_generator.generate_perf_tests_from_all_xml(parsed_cmd_args)



