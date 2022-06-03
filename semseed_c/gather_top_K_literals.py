from argparse import ArgumentParser
from glob import iglob
from collections import defaultdict
from typing import List, Iterable
from tqdm import tqdm
from clang.cindex import Index, TranslationUnit, CursorKind, SourceLocation, SourceRange, TokenKind
from multiprocessing import Pool, cpu_count
from itertools import islice
import json


def compute_counter(path: Iterable[str]):
    counter = defaultdict(int)

    try:
        ast = TranslationUnit.from_source(path, args=['-xcpp-output'])
        for token in ast.cursor.get_tokens():
            if token.kind == TokenKind.LITERAL:
                counter[token.spelling] += 1
    except Exception as err:
        print(err)

    return counter


def gather_to_k_literals(input_directory: str, output_path: str, k: int, file_extension: str):
    source_files = list(filter(lambda path: path.endswith(file_extension),
                               map(str, iglob(f'{input_directory}/**', recursive=True))))

    counter = defaultdict(int)

    with Pool(cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(compute_counter, source_files, chunksize=200), total=len(source_files)):
            counter.update(result)

    result = []
    for lit, occ in tqdm(islice(sorted(counter.items(), key=lambda item: item[1], reverse=True), k)):
        result.append(lit)

    with open(output_path, 'w') as output_file:
        json.dump(result, output_file, indent=4)


def main():
    parser = ArgumentParser()
    parser.add_argument(
        '--in_dir',
        type=str,
        default='../benchmarks/__top_c_repos',
        help='The directory containing files to gather literals'
    )
    parser.add_argument(
        '--out_path',
        type=str,
        default='../benchmarks/topK_c_literals.json',
        help='The directory containing files to gather literals'
    )
    parser.add_argument(
        '--k',
        type=int,
        default=10000,
        help='select top K tokens'
    )
    parser.add_argument(
        '--file_extension',
        type=str,
        default='.c',
        help='File extension used to filter files'
    )
    args = parser.parse_args()
    print(args)

    gather_to_k_literals(args.in_dir, args.out_path, args.k, args.file_extension)


if __name__ == '__main__':
    main()
