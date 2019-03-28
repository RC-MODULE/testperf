import os


def get_funcs_without_test(funcs_for_test, path_to_tests):
    funcs_with_test = [test_func + '\n' for test_func in os.listdir(path_to_tests)]
    return list(set(funcs_for_test) - set(funcs_with_test))


def get_funcs_without_perf_table(funcs_for_test, path_to_tables):
    funcs_with_table = [perf_table[:-2] for perf_table in os.listdir(path_to_tables)]
    return list(set(funcs_for_test) - set(funcs_with_table))


def generate_log(log_path, init_funcs, funcs_for_test, funcs_without_table):
    with open(os.path.join(log_path, "init_funcs.log"), 'a') as init_log:
        init_log.writelines(init_funcs)
    with open(os.path.join(log_path, "funcs_for_test.log"), 'a') as test_log:
        test_log.writelines(funcs_for_test)