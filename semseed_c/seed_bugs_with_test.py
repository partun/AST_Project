from sre_constants import SUCCESS
from unittest import result
from run_bug_seeding import run_bug_seeding
import subprocess
import random
from time import time
import argparse
from lib.util.argument_utils import read_arguments

def main():
    parser = argparse.ArgumentParser(
        prog='python run_bug_seeding.py',
        description="Provide the proper directories where bugs may be seeded",
        epilog="You must provide directories"
    )
    in_dir, out_dir, working_dir, stats_dir, bug_seeding_patterns, k_freq_lit, file_extension = read_arguments(parser)

    # subprocess.run(
    #             ['rm','-r','/home/dominic/project_code/SemSeed/benchmarks/bug_seeding_output/*']
    #         )

    i = 0
    stop_after = 1

    with open('results.txt', 'w') as result_file:

    
        while True:
            
            random.seed(time())
            i_out_dir = f'{out_dir}_{i}'
            run_bug_seeding(in_dir, i_out_dir, working_dir, stats_dir, bug_seeding_patterns, k_freq_lit, file_extension)

            # test if programm is valid

            try:
                # subprocess.run(['make', 'clean'], check=True, cwd='../benchmarks/bug_seeding_output/__mutated_version_0/lua-5.4.4/')

                # compile lua
                # subprocess.run(['make'], check=True, cwd=f'{i_out_dir}/__mutated_version_0/lua-5.4.4/')

                # compile sqlite
                subprocess.run(
                    [
                        #'CC=afl-clang-fast CFLAGS="$CFLAGS -DSQLITE_MAX_LENGTH=128000000',
                        #'CFLAGS="$CFLAGS -DSQLITE_MAX_LENGTH=128000000 -DSQLITE_MAX_SQL_LENGTH=128000000 -DSQLITE_MAX_MEMORY=25000000 -DSQLITE_PRINTF_PRECISION_LIMIT=1048576 -DSQLITE_DEBUG=1 -DSQLITE_MAX_PAGE_COUNT=16384"',
                        './configure', '--disable-shared', '--enable-rtree'
                    ],
                    check=True, cwd=f'{i_out_dir}/__mutated_version_0/sqlite/'
                )
                subprocess.run(['make'], check=True, cwd=f'{i_out_dir}/__mutated_version_0/sqlite/')
                print('success')

                result_file.write(f'success: {i}\n')
                stop_after -= 1
                if stop_after < 0:
                    return
            except subprocess.CalledProcessError:
                # subprocess.run(
                #     ['rm','-r','/home/dominic/project_code/SemSeed/benchmarks/bug_seeding_output/*'],
                #     check=True, shell=True
                # )
                result_file.write(f'failed: {i}\n')
            
            i += 1
    


if __name__ == '__main__':
    main()