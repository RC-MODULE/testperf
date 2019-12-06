from xml.dom import minidom
from xml.parsers import expat
import collections


def open_xml(xml_name):
    try:
        md = minidom.parse(xml_name)
    except expat.ExpatError as err:
        raise SyntaxError
    return md


def get_group_name(xml_doc):
    group_name_tag = xml_doc.getElementsByTagName('compoundname')
    return group_name_tag[0].firstChild.data


def get_perf_scripts(xml_doc):
    #  Функция ищет в переданном ей xml-файле тег testperf.
    #  В этом теге заключена информации сценария производительности, которую и достает данная функция.
    #  Функция принимает на в качестве параметра открытый xml-файл.
    testperf_tag = xml_doc.getElementsByTagName('testperf')

    if not testperf_tag:
        raise Exception("hasn't a testperf script")
    perf_scripts_list = [collections.OrderedDict() for i in enumerate(testperf_tag)]

    for map_num, perf_script in enumerate(testperf_tag):
        for node in perf_script.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                param_type = node.getAttribute('type')
                if node.tagName == 'param':
                    param_name = node.getAttribute('name').strip()
                    values = node.firstChild.data.strip()
                else:
                    if node.tagName == 'size':
                        param_name = 'custom_size_name_fig_podberesh'
                    else:
                        param_name = node.tagName
                    values = node.firstChild.data.strip()
                perf_scripts_list[map_num][(param_name, param_type)] = values

    #  Функция возвращает список словарей.
    #  Каждый элемент списка (словарь) описвает отдельный сценарий производительности для группы функций в пределах
    #  одного xml-файла.
    #  Ключами таких словарей являются кортежи из 2-х элементов (название параметра и тип параметра) для группы функций, а значения словаря это значения
    #  этих параметров, заданных в сценариях производительнрости.
    return perf_scripts_list


def get_funcs_prototypes(xml_doc):
    funcs_prototypes = {}
    elements = xml_doc.getElementsByTagName('memberdef')
    for element in elements:
        param = element.childNodes[3].firstChild.data
        value = element.childNodes[5].firstChild.data
        funcs_prototypes[param] = value
    return funcs_prototypes
