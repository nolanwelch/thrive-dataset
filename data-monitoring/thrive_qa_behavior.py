import sys
import os
import pandas as pd
from glob import glob
import re
from datetime import datetime

dataset_path = "/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/" # mofify if your behavioral data is in another folder
session = "s1_r1" # modify if using for another session
subject_data_paths = sorted(glob(f"{dataset_path}sub-*"))
pattern = r'sub-(\d{7})' # regex to take subject id
extensions = ['.log', '.csv', '.psydat']
n_blocks = 20
n_trials = 40
all_trial_count = n_blocks * n_trials
some_trial_count = 100

sys.stdout = open(f"qa_log_behavior_{datetime.now().strftime('%d-%m-%Y_%H_%M_%S')}.txt", "wt") # write a log

for path in subject_data_paths:
    deviation = 0
    print("")
    sub = re.search(pattern, path).group(1)
    subject_folder = f"{dataset_path}sub-{sub}/{session}/psychopy/"
    sub_psychopy_files = sorted(glob(f"{subject_folder}*"))
    
    if "deviation.txt" in os.listdir(subject_folder): # first check if a deviation present
        deviation = 1
        # print(f"sub-{sub} has deviation.txt in their psychopy folder! Check that subject manually!")
    
    if len(sub_psychopy_files) == 3: # best case scenario if only 3 files are present
        found_extensions = {ext: False for ext in extensions}
        for psychopy_file in sub_psychopy_files:
            _, ext = os.path.splitext(psychopy_file)
            if ext in found_extensions:
                found_extensions[ext] = True
        if sum([item[1] for item in list(found_extensions.items())]) == 3: # ideal case, all 3 files are correct extension
            try:
                psychopy_data = pd.read_csv(glob(f"{subject_folder}*.csv")[0])
                start_index = psychopy_data["task_blockText.started"].first_valid_index()
                psychopy_data = psychopy_data.iloc[start_index:, :].dropna(subset = "middleStim")
                psychopy_data = psychopy_data[psychopy_data["conditionText"].isin(["Observed", "Alone"])].reset_index(drop=True) # check num of trials
                if psychopy_data.shape[0] == all_trial_count:
                    print(f"sub-{sub} has ALL trial data! PASSED!")
                elif psychopy_data.shape[0] < all_trial_count and psychopy_data.shape[0] > some_trial_count:
                    print(f"sub-{sub} has SOME trial data! FAILED!")
                else:
                    print(f"sub-{sub} has NO trial data! FAILED!")
            except:
                print(f"sub-{sub} file FAILS to load!")
        else:
            print(f"sub-{sub} has 3 files BUT not with correct extensions! FAILED!")
    elif len(sub_psychopy_files) != 3:
        sub_trial_count = 0
        if not deviation: # do not continue if not all files are correct AND no deviation
            print(f"sub-{sub} has incorrect number of files and no deviation was found! FAILED!")
        elif deviation: # if deviation, try counting all trials from all csvs in the folder
            sub_csv_files = sorted(glob(f"{subject_folder}*.csv"))
            for csv_fname in sub_csv_files:
                try:
                    psychopy_data = pd.read_csv(csv_fname)
                    if "task_blockText.started" in list(psychopy_data.columns): # count trials from only task-related csv
                        start_index = psychopy_data["task_blockText.started"].first_valid_index()
                        psychopy_data = psychopy_data.iloc[start_index:, :].dropna(subset = "middleStim")
                        psychopy_data = psychopy_data[psychopy_data["conditionText"].isin(["Observed", "Alone"])].reset_index(drop=True) # check num of trials
                        sub_trial_count += psychopy_data.shape[0]
                    else:
                        pass # skip if not task-related csv
                except:
                    print(f"sub-{sub} has deviation and file FAILS to load!")
            if sub_trial_count == all_trial_count:
                print(f"sub-{sub} has deviation but ALL trial data! PASSED!")
            elif sub_trial_count < all_trial_count and sub_trial_count > some_trial_count:
                print(f"sub-{sub} has deviation and SOME trial data! FAILED!")
            else:
                print(f"sub-{sub} has deviation and NO trial data! FAILED!")
