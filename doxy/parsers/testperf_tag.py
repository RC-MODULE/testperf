#######################################################
# Software designer: A.Brodyazhenko
# Year: 2019
# Content: Class for a testperf tag parsing. This xml tag is unique.
#######################################################

from collections import namedtuple


class TestperfTagParser:
    def __init__(self, testperf_tag):
        self.__testperf_tag = testperf_tag
        self.__perf_script = namedtuple('PerfScript', ['arguments_values',
                                                        'arguments_names',
                                                        'arguments_types',
                                                        'size',
                                                        'initialization_func',
                                                        'deinitialization_func'])
        self.__perf_script.arguments_values = []
        self.__perf_script.arguments_names = []
        self.__perf_script.arguments_types = []
        self.__perf_script.size = ''
        self.__perf_script.initialization_func = ()
        self.__perf_script.deinitialization_func = ()

    def parse_testperf_tag(self):
        self.parse_arguments_types()
        self.parse_arguments_names_and_values()
        self.parse_initialization_func()
        self.parse_deinitialization_func()
        self.parse_size()

    def get_perf_script(self):
        return self.__perf_script

    def parse_arguments_names_and_values(self):
        for node in self.__testperf_tag.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if node.tagName == 'param':
                    argument_name = node.getAttribute('name').strip()
                    self.__perf_script.arguments_names.append(argument_name)

                    values = node.firstChild.data.strip().replace(' ', ', ')
                    self.__perf_script.arguments_values.append(values)

    def parse_arguments_values(self):
        for node in self.__testperf_tag.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if node.tagName == 'param':
                    values = node.firstChild.data.strip().replace(' ', ', ')
                    self.__perf_script.arguments_values.append(values)

    def parse_arguments_types(self):
        for node in self.__testperf_tag.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                argument_type = node.getAttribute('type')
                self.__perf_script.arguments_types.append(argument_type)

    def parse_arguments_names(self):
        for node in self.__testperf_tag.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if node.tagName == 'param':
                    argument_name = node.getAttribute('name').strip()
                    self.__perf_script.arguments_names.append(argument_name)

    def __parse_single_tag(self, tag_name):
        for node_number, node in enumerate(self.__testperf_tag.childNodes):
            if node.nodeType == node.ELEMENT_NODE:
                if node.tagName == tag_name:
                    data_from_tag_and_pos = (node.firstChild.data.strip(), int(node_number / 2))
                    return data_from_tag_and_pos
        return None

    def parse_size(self):
        size_tag = self.__parse_single_tag('size')
        if size_tag is not None:
            self.__perf_script.size = size_tag[0]
        else:
            self.__perf_script.size = None

    def parse_initialization_func(self):
        self.__perf_script.initialization_func = self.__parse_single_tag('init')

    def parse_deinitialization_func(self):
        self.__perf_script.deinitialization_func = self.__parse_single_tag('deinit')

if __name__ == '__main__':
    pass
