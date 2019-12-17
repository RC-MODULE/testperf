
from xml.dom import minidom
from xml.parsers import expat


class DoxyXmlParser:
    def __init__(self, path_to_doxy_xml):
        try:
            self.__opened_doxy_xml = minidom.parse(path_to_doxy_xml)
        except expat.ExpatError:
            raise SyntaxError

        group_name_tag = self.__opened_doxy_xml.getElementsByTagName('compoundname')
        self.__compoundname_tag = group_name_tag[0].firstChild.data
        self.__memberdef_tags = self.__opened_doxy_xml.getElementsByTagName('memberdef')
        self.__testperf_tags = self.__opened_doxy_xml.getElementsByTagName('testperf')

    def get_compoundname_tag(self):
        return self.__compoundname_tag

    def get_memberdef_tags(self):
        return self.__memberdef_tags

    def get_testperf_tags(self):
        return self.__testperf_tags

if __name__ == '__main__':
    pass
