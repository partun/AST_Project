from lib.BugFixes import MongoDB
from lib.CodeAnalysis import CodeAnalysis
import pygit2 as git
from pprint import pprint


def extract_bug_pattern(commit_id: str) -> None:

    # get the commit from mongodb
    mongo = MongoDB()
    commit = mongo.get_commit(commit_id)
    if commit is None:
        print(f'cloud not find commit with id: {commit_id}')

    for change in commit['single_line_changes']:
        change['analysis_report'] = 'Not Analysed'

        repo = git.Repository(f"../{commit['local_repo_path']}")

        fixed_file = repo.revparse_single(
            f"{commit['commit_hash']}:{change['new_file']['path']}")

        CodeAnalysis.from_source(
            commit['local_repo_path'] + change['new_file']['path'],
            fixed_file.read_raw()
        )

        # pprint(fixed_file.read_raw())

        buggy_file = repo.revparse_single(
            f"{commit['parent_hash']}:{change['old_file']['path']}")

        # pprint(buggy_file.read_raw())
