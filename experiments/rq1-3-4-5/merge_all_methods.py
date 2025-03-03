import os
import pandas as pd
import json
import Levenshtein

    

def check_action_in_groundtruth(groundtruth, soa):
    action_in_gt = []
    line_actions = soa.split('\n')
    actions = []
    found_gts = []
    for line in line_actions:
        if not '"' in line:
            continue
        action = line.split('"')[1]
        actions.append(action)
    for action in actions:
        if action not in groundtruth or action in found_gts:
            action_in_gt.append(False)
        else:
            action_in_gt.append(True)
            found_gts.append(action)
    return action_in_gt
    

def get_task_by_task_desc(df, app_name, task_desc, df_path=None):
    original_task_desc = task_desc
    original_df = df.copy(deep=True)
        
    candidates = df[(df['app_name'] == app_name) & (df['task_desc'] == task_desc)]
    if len(candidates) > 0:
        return candidates.iloc[0] 
    
    app_name = app_name.lower()
    task_desc = task_desc.lower().strip()
    # lower case all the task_desc and app_name in the dataframe
    df['task_desc'] = df['task_desc'].apply(lambda x: x.lower().strip())
    df['app_name'] = df['app_name'].apply(lambda x: x.lower())
    
    df = df[df['app_name'] == app_name]
    # get the task with the same task_desc and app_name
    candidates = []
    found_ids = []
    for index, row in df.iterrows():
        df.at[index, 'distance'] = Levenshtein.distance(row['task_desc'], task_desc)
        if row['task_desc'] == task_desc or task_desc in row['task_desc'] or row['task_desc'] in task_desc:
            candidates.append(row)
            found_ids.append(index)
            break
        
    if len(candidates) == 0:
        return None
    
    # get the row with the minimum distance
    min_distance = min(df['distance'])
    candidates = df[df['distance'] == min_distance]
    if len(candidates) == 0:
        return None
    
    if len(candidates) > 1:
        candidates = candidates[candidates.index.isin(found_ids)]
        
    if len(candidates) == 0:
        return None
    
    return candidates.iloc[0]


# 'autodroid', 'droidagent', 'guardian', 'visidroid', 
methods = ['guardian','droidagent', 'autodroid',  'visidroid',  'visidroid_no_mem', 'visidroid_no_vision',]
        #    'visidroid_no_vision']
        
# methods = ["visidroid", ]
gt = r'experiments\rq1-3-4-5\groundtruth'

gt_df = pd.read_excel(os.path.join(gt, 'all_tasks.xlsx'))
gt_df = gt_df[gt_df['app_name']!= 'firefox']

merged_df = gt_df.copy(deep=True)
merged_df = merged_df.rename(columns={'soa': 'groundtruth'})

# add columns for each method
for method in methods:
    merged_df[method] = None
    merged_df[f"{method}_strict_eval"] = None

method_dfs = {}
not_founds = {}
founds = {}
for method in methods:
    base_dir = os.path.join(r'experiments\rq1-3-4-5\methods', method)
    method_dfs[method] = pd.read_excel(os.path.join(base_dir, 'all_tasks.xlsx'))
    not_founds[method] = []
    founds[method] = []
    
for index, row in merged_df.iterrows():
    task_desc = row['task_desc']
    app_name = row['app_name']

    for method in methods:    
        base_dir = os.path.join(r'experiments\rq1-3-4-5\methods', method)
        task = get_task_by_task_desc(method_dfs[method], app_name, task_desc, os.path.join(base_dir, 'all_tasks_.xlsx'))
        if task is None and (method == 'visidroid_no_vision' or method == 'visidroid_no_mem'):
            task = get_task_by_task_desc(method_dfs['visidroid'], app_name, task_desc, os.path.join(base_dir, 'all_tasks_.xlsx'))
        if task is None:
            not_founds[method].append(f"{app_name}: {task_desc}")
            continue
        else:
            founds[method].append(task)
            merged_df.at[index, method] = task['soa']
            # merged_df.at[index, f"valid"] = task['VALID']
            # merged_df.at[index, f"optimal"] = task['OPTIMAL']
            # merged_df.at[index, f"note"] = task['NOTE']
            
            # if merged_df.at[index, method] == row['groundtruth']: set eval to 1
            if not isinstance(row['groundtruth'], str) or not isinstance(task['soa'], str):
                continue
            gt = row['groundtruth'].replace(' ', '').replace('-', '').replace('_', '').replace('\n', '')
            candidate = task['soa'].replace(' ', '').replace('-', '').replace('_', '').replace('\n', '')
            merged_df.at[index, f"{method}_strict_eval"] = 1 if gt == candidate else 0
            merged_df.at[index, f"{method}_action_eval"] = json.dumps(check_action_in_groundtruth(row['groundtruth'], task['soa']))
            
            if isinstance(task['soa'], str):
                if merged_df.at[index, method][-1] != '\n':
                    merged_df.at[index, method] += '\n'
                merged_df.at[index, method] += f"- ACTION {len(merged_df.at[index, method].split('\n'))}: Task completed?\n"

with open('not_founds.txt', 'w') as f:
    for method in methods:
        f.write(f"{method}\n")
        for task in not_founds[method]:
            f.write(f"{task}\n")
        f.write('=======\n')
        
# for method in methods:
#     not_found_in_gt = []
#     for index, row in method_dfs[method].iterrows():
#         task_desc = row['task_desc']
#         app_name = row['app_name']
#         task = get_task_by_task_desc(merged_df, app_name, task_desc)
#         if task is None:
#             not_found_in_gt.append(f"{app_name}: {task_desc}")
#     with open(f'not_founds_{method}.txt', 'w') as f:
#         for task in not_found_in_gt:
#             f.write(f"{task}\n")
        
merged_df.to_excel('merged_all_tasks_.xlsx', index=False)