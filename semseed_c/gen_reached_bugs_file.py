import json
from glob import glob
from pathlib import Path


def main(pattern):
    paths = glob(pattern)

    print(f'found {len(paths)} bug meta data files')

    bug_ids = []

    for path in paths:
        with open(path, 'r') as meta_file:
            meta_datas = json.load(meta_file)

            for m in meta_datas:

                bug_ids.append(m['bug_id'])
                print(f'{m["bug_id"]}: {Path(path).name}')


    assert len(bug_ids) == len(set(bug_ids))
    print(f'found {len(bug_ids)} bugs')

    output = ','.join((f'{i}:0' for i in bug_ids))

    print(output)

    with open('bugs.txt', 'w') as bugs_file:
        bugs_file.write(output)


if '__main__' == __name__:
    main('/home/dominic/project/targets/lua/buggy/bugs/*.json')