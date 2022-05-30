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
from typing import List
import random
from pathlib import Path
from lib.bug_seeding.extract_node_data import analyze_target_code


def prepare_a_js_file_for_seeding_bug(target_js_file_path: str, out_json_file_path: str) -> str:
    """
    Prepare a JS file for seeding bugs by converting JS file to AST nodes.
    The functions creates a Nodejs process to extract the required data.
    :param target_js_file_path: The input JS file that will be converted to AST node representations
    :param out_json_file_path:
    :return:
    """

    # todo: maybe start timeout timer

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
    target_js_dir: str, abstracted_out_dir: str, source_code_file_pattern: str,
    num_of_files: int = -1
) -> None:
    """
    Given a directory of JS files, format the code and run static analysis to extract nodes
    from the code.
    :param num_of_files: Select only 'num_of_files' files from 'abstracted_out_dir' once it is ready
    :param target_js_dir:

    :param abstracted_out_dir:
    :return:
    """
    fs.create_dir_list_if_not_present([abstracted_out_dir])

    print(" Reading  files in {}".format(target_js_dir))
    all_target_js_files = sorted(Path(target_js_dir).rglob(source_code_file_pattern))
    all_target_js_files = [str(pth) for pth in all_target_js_files if pth.is_file()]

    # Some datasets might have duplicate files. We want to remove the duplicates
    # We do not need to remove duplicates
    # print(" Removing duplicates from {} files in benchmarks".format(len(all_target_js_files)))
    # duplicate_file_groups = fs.read_json_file('benchmarks/js150-duplicates.json')
    # all_target_js_files = remove_duplicates(
    #     file_list=all_target_js_files, duplicate_file_groups=duplicate_file_groups)

    if num_of_files > 1:
        random.seed(100)
        random.shuffle(all_target_js_files)
        all_target_js_files = all_target_js_files[:num_of_files]
    print(" Total number of files in benchmark is {}".format(len(all_target_js_files)))

    def create_out_file_path(target_js_file_path: str) -> str:
        pure_file_name = os.path.splitext(os.path.basename(target_js_file_path))[0]
        return os.path.join(abstracted_out_dir, f'{pure_file_name}.json')

    target_js_files_and_out_paths = [
        (target_js_file_path, create_out_file_path(target_js_file_path))
        for target_js_file_path in all_target_js_files
    ]
    if cpu_count() > 4:
        with Pool(processes=cpu_count()) as p:
            with tqdm(total=len(all_target_js_files)) as pbar:
                pbar.set_description_str(desc="Preparing files ...", refresh=False)
                for i, execution_errors in tqdm(
                        enumerate(p.imap_unordered(
                            prepare_a_js_file_for_seeding_bug_multiprocessing,
                            target_js_files_and_out_paths, chunksize=10
                        ))):
                    # print(execution_errors)
                    pbar.update()
                p.close()
                p.join()
    else:
        for target_file, out_file in tqdm(
            target_js_files_and_out_paths,
            desc='Preparing JS files *** Sequentially ***'
        ):
            prepare_a_js_file_for_seeding_bug(
                target_js_file_path=target_file, out_json_file_path=out_file)
