from subprocess import run
from glob import glob
from tqdm import tqdm


"""
run all the generated test cases to see witch bug are reached
"""



def main(test_cases_folder_path, target_path):

    
    for path in tqdm(glob(test_cases_folder_path)):
        if path.endswith('.txt'):
            print(f'skipping {path}')
            continue

        result = run([f'cat "{path}" | {target_path}'], cwd='/home/dominic/project/targets/lua/buggy/lua-testing', capture_output=True, shell=True)
        
        if result.returncode == 0:
            # did not crash
            print(f'{path}:')
            print(result.stdout)
        # else:
        #     print(result.stderr)





if __name__ == '__main__':
    # main('/home/dominic/project/targets/lua/buggy/lua-honggfuzz/crashes/*', '/home/dominic/project/targets/lua/buggy/lua-testing/lua/src/lua')
    # main('/home/dominic/project/targets/lua/buggy/lua-afl/output_i/crashes/*', '/home/dominic/project/targets/lua/buggy/lua-testing/lua/src/lua')
    main('/home/dominic/project/targets/lua/buggy/lua-aflplusplus/output_i/default/crashes/*', '/home/dominic/project/targets/lua/buggy/lua-testing/lua/src/lua')
