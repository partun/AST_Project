"""

Created on 01-April-2020
@author Jibesh Patra

"""
from lib.bug_seeding.bug_seeding_approaches.SemSeed.SemSeedBugs import SemSeedBugs
import lib.bug_seeding.static_analysis_utils as static_analysis_utils
import lib.util.fileutils as fs
import random
from tqdm import tqdm
from pathlib import Path
from typing import List
import os
import jsbeautifier

random.seed(a=42)


def seed_bugs_to_a_file_multiprocessing(args):
    """
    The multiprocessing wrapper of seed_bugs_to_a_file function
    :param args:
    :return:
    """
    file, bug_seeding_patterns, K_most_frequent_literals, MAX_TRIES_TO_SEED_BUGS, MAX_BUGS_TO_SEED, in_dir, out_dir = args
    return seed_bugs_to_a_file(file, bug_seeding_patterns, K_most_frequent_literals,
                               MAX_TRIES_TO_SEED_BUGS, MAX_BUGS_TO_SEED, in_dir, out_dir)


def seed_bugs_to_a_file(file: str,
                        bug_seeding_patterns: List,
                        K_most_frequent_literals: List,
                        MAX_LOCATIONS_TO_TRY_TO_SEED_BUGS: int,
                        MAX_BUGS_TO_SEED,
                        in_dir: str,
                        out_dir: str,
                        file_extention: str = '.c') -> int:
    """
    Given a file seed bugs to it. The expected file is a JSON file rather than a JS file. It is expected
    that the input JS file has been analysed before and a corresponding JSON file has been created
    :param file: the corresponding JSON file of the JS file where bugs need to be seeded
    :param bug_seeding_patterns:
    :param K_most_frequent_literals:
    :param MAX_LOCATIONS_TO_TRY_TO_SEED_BUGS:
    :param out_dir: A path where the mutate code will be written
    :return: The count of bugs that could be seeded to the file
    """

    ATTEMPTS_TO_FILL_UNBOUND_TOKENS = 2

    num_of_locations_that_could_be_mutated = 0

    target_js_file_analysed = fs.read_json_file(file)
    if len(target_js_file_analysed) == 0:  # The static analysis could not finish properly
        return num_of_locations_that_could_be_mutated
    possible_bug_seeding_locations = target_js_file_analysed['nodes']

    # We do not want to select the first 'n' locations and try to seed bugs. Rather we randomly
    # choose 'n' locations
    random.shuffle(possible_bug_seeding_locations)
    if MAX_LOCATIONS_TO_TRY_TO_SEED_BUGS > 1:
        possible_bug_seeding_locations = possible_bug_seeding_locations[:MAX_LOCATIONS_TO_TRY_TO_SEED_BUGS]

    file_name = Path(file).name

    # Go through each seeding pattern available from the bug seeding patterns
    matching_locations = []
    for seeding_pattern in tqdm(
            bug_seeding_patterns, position=1, ncols=100, ascii=" #",
            desc='Trying to apply pattern', postfix={'file': file_name}
    ):
        # For each location in the file, try to seed a bug
        for target_location in possible_bug_seeding_locations:
            # ------------------------ SemSeed -----------------------------------------
            bug_seeding = SemSeedBugs(
                bug_seeding_pattern=seeding_pattern,
                target_location=target_location,
                file_path=target_js_file_analysed['file_path'],
                similarity_threshold=0.3,
                K=ATTEMPTS_TO_FILL_UNBOUND_TOKENS,
                available_identifiers=target_js_file_analysed['functions_to_idf'],
                available_literals={'K_most_frequent_literals': K_most_frequent_literals,
                                    'all_literals_in_same_file': static_analysis_utils.get_all_tokens_in_file(
                                        target_js_file_analysed['range_to_lit'])},
                scope_of_selection='function'
            )

            # Check if the seeding pattern and the target locations match
            if bug_seeding.is_matching_token_sequence():
                matching_locations.append(bug_seeding)

    random.shuffle(matching_locations)
    # randomly select MAX_BUGS_TO_SEED different location
    selected_locations = dict()
    for bug_seeding in matching_locations:
        bug_location = bug_seeding.get_target_locations()
        assert bug_location.is_one_line()

        if not bug_location.start_line in selected_locations:
            selected_locations[bug_location.start_line] = bug_seeding
            if len(selected_locations) >= MAX_BUGS_TO_SEED:
                # we have enought bug locations
                break

    # apply the bug to the file
    bug_seeded_meta_data = dict()
    mutated_file_lines = dict()
    target_file_path = target_js_file_analysed['file_path']

    with open(target_js_file_analysed['file_path'], 'r') as original_file:
        original_file_iter = iter(enumerate(
            original_file.readlines(),
            start=1
        ))
        for bug_idx, bug_seeding in enumerate(
                sorted(selected_locations.values(), key=lambda x: x.get_target_locations().start_line)):
            # The mutated token sequences is only the 'mutated' target location token sequence
            # We may get multiple sequences based on K. If K=2 and there is only one
            # unbound token, we get 2 sequences
            target_location = bug_seeding.get_target_locations()
            mutated_token_sequences = bug_seeding.apply_pattern()
            if len(mutated_token_sequences) <= 0:
                continue

            # store meta date for the seeded bugs
            for ms_idx, mutated_sequence in enumerate(mutated_token_sequences):
                # token_sequence_after_seeding_bug = bug_seeding.replace_target_with_mutated_token_sequence(
                #     token_list=target_js_file_analysed['token_list'],
                #     token_range_list=target_js_file_analysed['token_range_list'],
                #     mutated_token_sequence=mutated_sequence)

                bug_seeded_meta_data.setdefault(ms_idx, []).append({
                    'index': ms_idx,
                    'range': str(target_location),
                    'target_token_sequence-Buggy': mutated_sequence,
                    'token_sequence_abstraction-Buggy': bug_seeding.bug_seeding_pattern['buggy'],
                    'num_of_available_identifiers_to_choose_from': len(
                        bug_seeding.identifiers_available_for_selecting_unbound_token),
                    'num_of_available_literals_to_choose_from': len(
                        bug_seeding.literals_available_for_selecting_unbound_token),
                    'seeding_pattern_url': bug_seeding.bug_seeding_pattern['url']
                })

            while True:
                try:
                    lineno, original_line = next(original_file_iter)
                    if lineno < target_location.start_line:
                        # no modification on this line
                        for ms_idx, _ in enumerate(mutated_token_sequences):
                            mutated_file_lines.setdefault(ms_idx, []).append(original_line)

                    elif lineno == target_location.start_line:
                        for ms_idx, mutated_sequence in enumerate(mutated_token_sequences):
                            before_modification = original_line[:target_location.start_col - 1]
                            after_modification = original_line[target_location.end_col - 1:]
                            # modify line

                            mutated_file = mutated_file_lines.setdefault(ms_idx, [])
                            mutated_file.append(f'// MODIFICATION {bug_idx} START\n')
                            mutated_file.append(
                                '// ORIGINAL LINE: "{}"\n'.format(original_line.replace("\n", ""))
                            )
                            mutated_file.append(
                                f'{before_modification} {" ".join(mutated_sequence)} {after_modification}'
                            )
                            mutated_file.append(f'// MODIFICATION {bug_idx} END\n')

                        # done with this bug
                        break

                except StopIteration:
                    print('ERROR: file was finished before last bug')

        # finish copying the original file
        while True:
            try:
                lineno, original_line = next(original_file_iter)
                for ms_idx in range(ATTEMPTS_TO_FILL_UNBOUND_TOKENS):
                    mutated_file_lines.setdefault(ms_idx, []).append(original_line)
            except StopIteration:
                break

        for ms_idx, lines in mutated_file_lines.items():
            mutated_file_path = Path(target_file_path.replace(
                in_dir, f'{out_dir}/__mutated_version_{ms_idx}'
            ))
            # create parent folders if they do not exist
            mutated_file_path.parent.mkdir(exist_ok=True, parents=True)
            with open(mutated_file_path, 'w') as mutated_file:
                mutated_file.writelines(lines)

        for ms_idx, stats in bug_seeded_meta_data.items():
            meta_file_path = Path(target_file_path.replace(
                in_dir, f'{out_dir}/__meta_data_{ms_idx}'
            ).replace(file_extention, '.json'))
            meta_file_path.parent.mkdir(exist_ok=True, parents=True)
            fs.writeJSONFile(data=stats, file_path=str(meta_file_path))

    return num_of_locations_that_could_be_mutated
