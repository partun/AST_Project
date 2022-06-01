import json
from lib.Extractor import Extractor
from lib.BugFixes import MongoDB
from lib.util.Watchdog import set_timeout


@set_timeout(30)
def analyze_target_code(input_file_path: str, output_file_path: str) -> None:
    extractor = Extractor.from_file(input_file_path)
    analysed_code = extractor.extract_specific_nodes()
    extractor.abstract_all_idf_and_lit(analysed_code)

    result_obj = {
        'nodes': analysed_code,
        'functions_to_idf': extractor.scope_to_idf,
        'functions_to_lit': extractor.scope_to_lit,
        'token_list': extractor.token_list,
        'token_range_list': extractor.token_range_list,
        'range_to_idf': {k: v['name'] for k, v in extractor.range_to_idf.items()},
        'range_to_lit': {k: v['value'] for k, v in extractor.range_to_lit.items()},
        'file_path': input_file_path
    }

    with open(output_file_path, 'w') as output_file:
        json.dump(MongoDB.make_obj_serializable(result_obj), output_file)


def test():
    analyze_target_code(
        '/home/steiner/eth/01_SS22/AST_AutomatedSoftwareTesting/Project/SemSeed/benchmarks/data/test.c',
        '/home/steiner/eth/01_SS22/AST_AutomatedSoftwareTesting/Project/SemSeed/benchmarks/data/test.json'
    )


if __name__ == '__main__':
    test()
