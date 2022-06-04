"""

Created on 25-March-2020
@author Jibesh Patra

Call nodejs to tokenize and convert files to their AST representations, tokenize etc.
"""
import os
import subprocess
from threading import Timer
import lib.util.fileutils as fs
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from typing import List, Tuple
import random
from pathlib import Path
import glob
from lib.bug_seeding.extract_node_data import analyze_target_code


def prepare_a_js_file_for_seeding_bug(target_js_file_path: str, out_json_file_path: str) -> str:
    """
    Prepare a JS file for seeding bugs by converting JS file to AST nodes.
    The functions creates a Nodejs process to extract the required data.
    :param target_js_file_path: The input JS file that will be converted to AST node representations
    :param out_json_file_path:
    :return:
    """

    try:
        analyze_target_code(target_js_file_path, out_json_file_path)
    except Exception as err:
        print(err)
        return str(err)


def remove_duplicates(file_list: List, duplicate_file_groups: List) -> List:
    """
    Given a list of files, and known duplicates, keep only one of the duplicates
    :param duplicate_file_groups:
    :param file_list:
    :return:
    """
    dup_files = set()
    for file_group in duplicate_file_groups:
        # Except the first file rest are all duplicates
        dup_files.update(file_group[1:])

    files_without_duplicates = []
    # Now, we remove the known duplicates
    root_dir = '/data/'
    # dup_files = set([os.path.join(root_dir, fp) for fp in dup_files])
    for fl_path in file_list:
        if fl_path.split(root_dir)[1] not in dup_files:
            files_without_duplicates.append(fl_path)
    return files_without_duplicates


def prepare_a_js_file_for_seeding_bug_multiprocessing(arg):
    target_js_file_path, out_json_file_path = arg
    prepare_a_js_file_for_seeding_bug(target_js_file_path, out_json_file_path)


def prepare_dir_for_seeding_bugs(
        target_dir: str, abstracted_out_dir: str, file_extension: str,
        num_of_files: int = -1
) -> Tuple[List[Path], List[Path]]:
    """
    Given a directory of JS files, format the code and run static analysis to extract nodes
    from the code.
    :param num_of_files: Select only 'num_of_files' files from 'abstracted_out_dir' once it is ready
    :param target_js_dir:

    :param abstracted_out_dir:
    :return: list analysed target paths, list non target paths
    """
    fs.create_dir_list_if_not_present([abstracted_out_dir])

    target_files = []
    non_target_files = []
    for path_str in glob.glob(f'{target_dir}/**', recursive=True):
        path = Path(path_str)
        if not path.is_file():
            # do not include directories
            continue

        if path_str.endswith(file_extension):
            target_files.append(path)
        else:
            non_target_files.append(path)

    if num_of_files > 0:
        random.seed(10)
        random.shuffle(target_files)
        filtered_target_files = target_files[:num_of_files]
        non_target_files.extend(target_files[num_of_files:])
    else:
        filtered_target_files = target_files

    print(f"target files: {filtered_target_files}")
    # print(f"non target files: {non_target_files}")

    def create_out_file_path(target_path: Path) -> str:
        return str(target_path).replace(target_dir, abstracted_out_dir).replace(file_extension, '.json')

    analysis_output_paths = [
        (str(path), create_out_file_path(path))
        for path in filtered_target_files
    ]

    if cpu_count() > 4:
        with Pool(processes=cpu_count()) as p:
            with tqdm(total=len(analysis_output_paths)) as pbar:
                pbar.set_description_str(desc="Preparing files ...", refresh=False)
                for i, execution_errors in tqdm(
                        enumerate(p.imap_unordered(
                            prepare_a_js_file_for_seeding_bug_multiprocessing,
                            analysis_output_paths, chunksize=10
                        ))):
                    # print(execution_errors)
                    pbar.update()
                p.close()
                p.join()
    else:
        for target_file, out_file in tqdm(
                analysis_output_paths,
                desc='Preparing files *** Sequentially ***'
        ):
            prepare_a_js_file_for_seeding_bug(
                target_js_file_path=target_file, out_json_file_path=out_file)

    return [Path(x[1]) for x in analysis_output_paths], non_target_files
