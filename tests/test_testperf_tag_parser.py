
import unittest
from doxy.parsers.xml import DoxyXmlParser
from doxy.parsers.testperf_tag import TestperfTagParser


class TestTestperfTagParser(unittest.TestCase):
    __doxy_xml_parser = DoxyXmlParser('for_test.xml')
    __testperf_tag = __doxy_xml_parser.get_testperf_tags()[0]
    __testperf_tag_parser = TestperfTagParser(__testperf_tag)

    def test_parse_arguments_names(self):
        self.__testperf_tag_parser.parse_arguments_names()
        perf_script = self.__testperf_tag_parser.get_perf_script()
        self.assertEqual(perf_script.arguments_names, ['x', 'X'])

    def test_parse_arguments_values(self):
        self.__testperf_tag_parser.parse_arguments_values()
        perf_script = self.__testperf_tag_parser.get_perf_script()
        self.assertEqual(perf_script.arguments_values, ['im1, im2, im3, im4, im5',
                                                        'im1, im2, im3, im4, im5'])

    def test_parse_arguments_types(self):
        self.__testperf_tag_parser.parse_arguments_types()
        perf_script = self.__testperf_tag_parser.get_perf_script()
        self.assertEqual(perf_script.arguments_types, ['', '', '', ''])

    def test_parse_size(self):
        self.__testperf_tag_parser.parse_size()
        perf_script = self.__testperf_tag_parser.get_perf_script()
        self.assertEqual(perf_script.size, '256')

    def test_parse_initialization_func(self):
        self.__testperf_tag_parser.parse_initialization_func()
        perf_script = self.__testperf_tag_parser.get_perf_script()
        self.assertEqual(perf_script.initialization_func, ('NmppsFFTSpec_32fcr* spec;\n                     '
                                                           'nmppsFFT256FwdInitAlloc_32fcr(&spec);', 0))

    def test_parse_deinitialization_func(self):
        self.__testperf_tag_parser.parse_deinitialization_func()
        perf_script = self.__testperf_tag_parser.get_perf_script()
        self.assertEqual(perf_script.deinitialization_func, None)

    def test_parse_testperf_tag(self):
        testperf_tag_parser = TestperfTagParser(self.__testperf_tag)
        testperf_tag_parser.parse_testperf_tag()
        perf_script = testperf_tag_parser.get_perf_script()
        self.assertEqual(perf_script.arguments_names, ['x', 'X'])
        self.assertEqual(perf_script.arguments_values, ['im1, im2, im3, im4, im5',
                                                        'im1, im2, im3, im4, im5'])
        self.assertEqual(perf_script.arguments_types, ['', '', '', ''])
        self.assertEqual(perf_script.initialization_func, ('NmppsFFTSpec_32fcr* spec;\n                     '
                                                           'nmppsFFT256FwdInitAlloc_32fcr(&spec);', 0))
        self.assertEqual(perf_script.deinitialization_func, None)


if __name__ == '__main__':
    unittest.main()