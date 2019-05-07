from xml.dom import minidom
import collections


def open_xml(xml_name):
    return minidom.parse(xml_name)


def get_group_name(xml_doc):
    group_name_tag = xml_doc.getElementsByTagName('compoundname')
    return group_name_tag[0].firstChild.data


def get_perf_scripts(xml_doc):
    #  Функция ищет в переданном ей xml-файле тег testperf.
    #  В этом теге заключена информации сценария производительности, которую и достает данная функция.
    #  Функция принимает на в качестве параметра открытый xml-файл.
    test_perf_tag = xml_doc.getElementsByTagName('testperf')
    if not test_perf_tag:
        raise Exception("hasn't a testperf script")
    perf_scripts_list = [collections.OrderedDict() for i in enumerate(test_perf_tag)]
    for map_num, perf_script in enumerate(test_perf_tag):
        for node in perf_script.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if node.tagName == 'param':
                    param = node.firstChild.data.strip()
                    value = node.getAttribute('values')
                else:
                    if node.tagName == 'size':
                        param = 'custom_size_name_fig_podberesh'
                    else:
                        param = node.tagName
                    value = node.firstChild.data.strip()
                perf_scripts_list[map_num][param] = value
    #  Функция возвращает список словарей.
    #  Ключами таких словарей являются названия ппараметров для группы функций, а значения словаря это значения
    #  параметров этих параметров, заданных в сценариях производительнрости.
    #  Каждый элемент списка (словарь) описвает отдельный сценарий производительности для группы функций в пределах
    #  одного xml-файла.
    return perf_scripts_list


def get_funcs_prototypes(xml_doc):
    funcs_prototypes = {}
    elements = xml_doc.getElementsByTagName('memberdef')
    for element in elements:
        param = element.childNodes[3].firstChild.data
        value = element.childNodes[5].firstChild.data
        funcs_prototypes[param] = value
    return funcs_prototypes
