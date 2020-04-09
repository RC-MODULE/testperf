

import unittest
from doxy.parsers.xml import DoxyXmlParser
from doxy.parsers.memberdef_tag import MemberdefTagParser


class TestMemberdefTagParser(unittest.TestCase):
    __doxy_xml_parser = DoxyXmlParser('for_test.xml')
    __memberdef_tag = __doxy_xml_parser.get_memberdef_tags()[0]
    __memberdef_tag_parser = MemberdefTagParser(__memberdef_tag)

    def test_parse_name(self):
        self.__memberdef_tag_parser.parse_name()
        func = self.__memberdef_tag_parser.get_function()
        self.assertEqual(func.name, 'nmppsFFT256Fwd_32fcr')

    def test_parse_prototype(self):
        self.__memberdef_tag_parser.parse_prototype()
        func = self.__memberdef_tag_parser.get_function()
        self.assertEqual(func.prototype, 'void nmppsFFT256Fwd_32fcr'
                                         '(const nm32fcr *x, nm32fcr *X, NmppsFFTSpec_32fcr *spec);')

    def test_parse_arguments_types_and_names(self):
        self.__memberdef_tag_parser.parse_arguments_types_and_names()
        func = self.__memberdef_tag_parser.get_function()
        self.assertEqual(func.arguments_types, ['nm32fcr *', 'nm32fcr *', 'NmppsFFTSpec_32fcr *'])
        self.assertEqual(func.arguments_names, ['x', 'X', 'spec'])

    def test_identify_point_type(self):
        memberdef_tag_parser = MemberdefTagParser(self.__memberdef_tag)
        memberdef_tag_parser.parse_arguments_types_and_names()
        memberdef_tag_parser.identify_point_type()
        func = memberdef_tag_parser.get_function()
        self.assertEqual(func.point_type, 'floating')

    def test_parse_memberdef_tag(self):
        memberdef_tag_parser = MemberdefTagParser(self.__memberdef_tag)
        memberdef_tag_parser.parse_memberdef_tag()
        func = memberdef_tag_parser.get_function()
        self.assertEqual(func.name, 'nmppsFFT256Fwd_32fcr')
        self.assertEqual(func.prototype, 'void nmppsFFT256Fwd_32fcr'
                                         '(const nm32fcr *x, nm32fcr *X, NmppsFFTSpec_32fcr *spec);')
        self.assertEqual(func.arguments_types, ['nm32fcr *', 'nm32fcr *', 'NmppsFFTSpec_32fcr *'])
        self.assertEqual(func.arguments_names, ['x', 'X', 'spec'])
        self.assertEqual(func.point_type, 'floating')

if __name__ == '__main__':
    unittest.main()
