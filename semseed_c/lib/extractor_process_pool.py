"""
@author Jibesh Patra
"""

import subprocess
from threading import Timer
from typing import Optional
import os
import json
import multiprocessing
from collections import Counter
from multiprocessing import Pool
from tqdm import tqdm
import lib.util.GitHubCommits as db
from lib.Extractor import extract_bug_pattern


def call_bug_extractor(commit_id) -> Optional[str]:
    try:
        return extract_bug_pattern(commit_id)
    except StopAsyncIteration as err:
        print('error while extraction bug pattern')
        print(err)
        return None
    except Exception as err:
        print(err)
        return 'exception'


def create_patterns_from_commits(selected_commit_range=None):
    '''
    Query the MongoDB database and select only those commits (commit_ids) where the number of files
    changed is one and the changes are single line changes.

    Next, the CallNodeJS for only those commits and create patterns.

    @param select_num_of_commits: -1 means select all commits.
    @return:
    '''

    # query filters
    num_of_files_changed = 1
    num_single_line_changes = 1
    query_obj = db.Commits.objects(
        num_files_changed=num_of_files_changed,
        num_single_line_changes=num_single_line_changes
    )
    print('Found %d records that has only %d file change and only %d single line change' %
          (query_obj.count(), num_of_files_changed, num_single_line_changes)
          )
    pks = json.loads(query_obj.only('pk').to_json()
                     )  # get only the primary keys

    # Now put all primary keys in a list.
    # The primary keys are nothing but commit hashes concatenated with the repository
    commit_ids = []

    for pk in pks:
        commit_ids.append(pk['_id'])

    if selected_commit_range is not None:
        print(
            f"Selecting only commits in the range {selected_commit_range} of {len(commit_ids)} available commits")
        commit_ids = commit_ids[selected_commit_range[0]:selected_commit_range[1]]

    # Parallel execution
    results_counter = Counter()
    with Pool(processes=multiprocessing.cpu_count() * 0 + 12) as p:
        with tqdm(total=len(commit_ids)) as pbar:
            pbar.set_description_str(
                desc="Extracting Patterns ", refresh=False)
            for i, result in tqdm(enumerate(p.imap_unordered(call_bug_extractor, commit_ids))):
                pbar.update()
                results_counter.update((result,))
            p.close()
            p.join()

    print(results_counter)
