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
    stop_after = 8

    with open('results.txt', 'w') as result_file:

    
        while True:
            
            random.seed(time())
            i_out_dir = f'{out_dir}_{i}'
            run_bug_seeding(
                in_dir, i_out_dir, working_dir, stats_dir, bug_seeding_patterns, k_freq_lit, file_extension,
                MAX_LOCATIONS_TO_TRY_TO_SEED_BUGS = 400,  # If -1 then try to seed everywhere
                MAX_BUGS_TO_SEED = 2,
                ATTEMPTS_TO_FILL_UNBOUND_TOKENS = 1
            )

            # test if programm is valid

            try:
                # subprocess.run(['make', 'clean'], check=True, cwd='../benchmarks/bug_seeding_output/__mutated_version_0/lua-5.4.4/')

                # compile lua
                subprocess.run(['make'], check=True, cwd=f'{i_out_dir}/__mutated_version_0/lua-5.4.4/')

                # compile libxml2
                # subprocess.run(['./autogen.sh',], check=True, cwd=f'{i_out_dir}/__mutated_version_0/libxml2/')
                # subprocess.run(['make'], check=True, cwd=f'{i_out_dir}/__mutated_version_0/libxml2/')

                # subprocess.run(['make'], check=True, cwd=f'{i_out_dir}/__mutated_version_0/cjson/')
                print('success')

                result_file.write(f'success: {i}\n')
                stop_after -= 1
                if stop_after <= 0:
                    return
            except subprocess.CalledProcessError:
                # subprocess.run(
                #     ['rm','-r','/home/dominic/project_code/SemSeed/benchmarks/bug_seeding_output/*'],
                #     check=True, shell=True
                # )
                result_file.write(f'failed: {i}\n')
            
            print(f'{stop_after} left')
            i += 1
    


if __name__ == '__main__':
    main()