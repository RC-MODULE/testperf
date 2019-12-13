
import os
import shutil

# cpptest = perftest


class BuildTemplateGenerator:
    def __init__(self, path_to_build_template):
        self.__path_to_build_template = path_to_build_template
        self.__cpptest_template_content = list()
        self.__cpptest_template_name = ''

    def get_cpptest_template_name(self):
        return self.__cpptest_template_name

    def copy(self, path_to_cpptest):
        # Функция копирует шаблон (Makefile, config.cfg, main.cpp) для сборки будущего теста в папку perf_<имя функции>.
        # Папка perf_<имя функции> создается этой функцие при копировании автоматически
        if not os.path.exists(path_to_cpptest):
            # shutil.rmtree(path_to_test)
            os.mkdir(path_to_cpptest)
        for file in os.listdir(self.__path_to_build_template):
            shutil.copy(os.path.join(self.__path_to_build_template, file), path_to_cpptest)
            shutil.copystat(os.path.join(self.__path_to_build_template, file), path_to_cpptest)

    def fetch_content_cpptest_template(self):
        build_dir_files_names = [file_name for file_name in os.listdir(self.__path_to_build_template)
                                 if file_name[-4:] == '.cpp' or file_name[-2:] == '.c']
        if not build_dir_files_names:
            raise FileNotFoundError
        for file_name in build_dir_files_names:
            with open(os.path.join(self.__path_to_build_template, file_name), 'r') as r_file:
                cpptest_template_content = r_file.readlines()
                for line in cpptest_template_content:
                    if 'int main' in line:
                        self.__cpptest_template_name = file_name
                        self.__cpptest_template_content = cpptest_template_content
                        return
        raise ValueError

    def generate_cpptest_beginning(self):
        self.fetch_content_cpptest_template()
        cpptest_beginning = ''.join(self.__cpptest_template_content)
        return_pos = cpptest_beginning.find('return')
        return cpptest_beginning[:return_pos].rstrip()