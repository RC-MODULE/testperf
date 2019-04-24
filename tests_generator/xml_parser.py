from xml.dom import minidom


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
    perf_scripts_list = []
    for perf_script in test_perf_tag:
        perf_script_dict = {}
        param_tag = perf_script.getElementsByTagName('param')
        values_tag = perf_script.getElementsByTagName('values')
        init_tag = perf_script.getElementsByTagName('init')
        freemem_tag = perf_script.getElementsByTagName('freemem')
        size_tag = perf_script.getElementsByTagName('size')
        if init_tag:
            perf_script_dict['init'] = init_tag[0].firstChild.data
        if freemem_tag:
            perf_script_dict['freemem'] = freemem_tag[0].firstChild.data
        if size_tag:
            perf_script_dict['custom_size_name_fig_podberesh'] = size_tag[0].firstChild.data
        for i in range(param_tag.length):
            param = param_tag[i].firstChild.data.strip()
            value = values_tag[i].firstChild.data.strip()
            perf_script_dict[param] = value
        perf_scripts_list.append(perf_script_dict)
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
