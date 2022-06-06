Semantic Bug Seeding: Adapted for C
---

We adapted these instructions form the SemSeed readme

  
## Requirements

- Node.js v14.17.0
- Python 3.8.5
- Ubuntu 22.04 LTS

Install **Node.js** and the required packages:

Node is only nessary if you want to download the repositories for extracted bug patterns

````shell
# You may install Node.js using nvm : https://github.com/nvm-sh/nvm
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
source ~/.bashrc

# Install Node.js 14
nvm install 14.17.0
# Install the required Node.js packages
npm install
````

Create a virtual environment for **Python** and install the required packages:

````shell
sudo apt install -y python3-dev # required for the 'fasttext' package
sudo apt install -y python3-venv

# Create a virtual environment
python3 -m venv semseed_venv
# Activate the virtual environment
source semseed_venv/bin/activate
# Install the required Python packages
pip install -r requirements.txt
````

We did use the same pre-trained token embeddings model as SemSeed. Its to big to include in these artefacts but it can be downloaded from [zenodo](https://zenodo.org/record/4901843).

---

## 1. Obtain Patterns for Seeding Bugs

You may **skip** this step and use the patterns used in the report available at
_benchmarks/bug_seeding_patterns.json_ for seeding bugs (Step 2).

Patterns can be obtained using two steps. The first step is to download all GitHub repositories, and the second step is to go through the commits of the downloaded repos and select and save only certain commits and to extract patterns from those commits.


### a) Download GitHub repositories

**Warning:** Downloading top-100 GitHub repositories will take large disk space.

The list of top GitHub C repositories is present at _benchmarks/__top_c_repos_ which is used by
default for downloading the repos. Alternatively, this list can be generated using the _getLinks()_ function from the
_semseed_c/repo_downloader.js_.

Download repos present in _benchmarks/top100_C_repos.json_:

````shell
node semseed_c/repo_downloader.js
````

Tip 💡:
The default number of repos to be downloaded is 100 and default download directory is _benchmarks/top_JS_repos_ both of
which can be changed in _repo_downloader.js_.

### b) Obtain seeding patterns from downloaded repositories

Assuming the repos have been downloaded in the default location i.e., _benchmarks/__top_c_repos_, the next step is to go
through each repo and save the commits.

How it works?

- For each repo, walk through the whole commit history starting from the most recent commit
- For each of the commits search the commit message for the presence of certain query terms
- If the query term exists, find a diff between the commit and its parent
- Go through each file in the diff and select only '.c' files
- For each of these '.c' files, find single line changes and save both the 'new content' and the 'old content' along
  with their line numbers to a MongoDB database
- Extract patterns from the commits and save back to the database.

Saving commits require installation of MongoDB and the creation of a user with proper rights. The steps are follows:

#### Install & Setup MongoDB

The simplest way to setup mongo is to use the _mongodb.docker-compose.yml_ file.

#### Go through commits and extract patterns

The next step is to go through the downloaded repos and extract commits where the commit message contains certain words
and then extract patterns from those commits. This can be done as follows:

```shell
cd semseed_c
python extract_bug_patterns.py
```

Tip 💡:

- To check if _extract_bug_patterns.py_ worked, you may enter the mongo shell (using the command ``mongo`` in a terminal) and issue the
  following command. This will randomly select a commit saved in the database and display on the screen.

  ```shell
  use SemSeed_github_commits_db;
  db.commits.aggregate([{ $sample: { size: 1 } }]);
  ```

  Alternatively, the data can be viewed using MongoDB Compass. The download and install instruction can be found:
  https://docs.mongodb.com/compass/current/install

#### Write the patterns to a file

Once the patterns have been extracted and saved to the database, the aggregate patterns can be saved to a JSON file
using the following script:

````shell
cd semseed_c
python aggregateChanges.py
````

---

## 2. Seed bugs using SemSeed

Given C files in _benchmarks/bug_seeding_input_, seed bugs:

````shell
cd semseeed_c
python3 run_bug_seeding.py
````

The result will be placed in the _buchmarks/bug_seeding_output_ directory.

Alternativly _seed_bugs_with_test.py_ script can be used to seed bug until a certain number of them compile successfully. Some parameters can be modified within this file.
---


## Generate bugs.txt file with a bunch json bug meta data files

modify desired path in the script

````shell
cd semseeed_c
python3 gen_reached_bugs_file.py
````


# Fuzzing targets

Each fuzzer has e script to start fuzzing within _targets/lua/buggy_. Some of the scripts may need to be modified with your fuzzer installation path.

The fuzzers afl, afl++ and honggfuzz have been installed with their respective installation instructions. 

# Reached Detection

For testing the _reached_detector.c_ replace the path to the bugs.txt file with your desired location. When used with a lua replace the version inside the _lua/src_ dirctory with the version with the correct bugs.txt path and recompile lua using the make command. We adapted the _lua/src/Makefile_ to also compile the _reached_detector.c_.

# Evaluation

For evalutaion open the jupyter notebook in the benchmarks folder and adjust the filenames to the files you want to evaluate.
