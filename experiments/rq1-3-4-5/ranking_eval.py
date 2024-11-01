import os
import shutil
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
    df['app_name'] = df['app_name'].apply(lambda x: x.lower().strip())
    
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
methods = ['visidroid_no_ranking']
        #    'visidroid_no_vision']
gt = 'groundtruth'

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
    base_dir = os.path.join('methods', method)
    method_dfs[method] = pd.read_excel(os.path.join(base_dir, 'all_tasks_replaced.xlsx'))
    not_founds[method] = []
    founds[method] = []

mapping = {}

new_df = pd.DataFrame(columns=merged_df.columns)
for index, row in merged_df.iterrows():
    task_desc = row['task_desc']
    app_name = row['app_name']
    hash = row['hash']

    for method in methods:    
        base_dir = os.path.join('methods', method)
        tasks = method_dfs[method][(method_dfs[method]['app_name'] == app_name) & (method_dfs[method]['hash'] == hash)]
        if len(tasks) == 0:
            input(f"Task not found: {app_name}: {task_desc}: {hash}")
        else:
            count = 0
            for index_, task in tasks.iterrows():
                founds[method].append(task)
                mapping[f"{task['app_name'].lower()}: {task['task_desc'].lower()}"] = app_name + ': ' + task_desc + ": " + hash
                merged_df.at[index, method] = task['soa']
                # if merged_df.at[index, method] == row['groundtruth']: set eval to 1
                if not isinstance(row['groundtruth'], str) or not isinstance(task['soa'], str):
                    continue
                gt = row['groundtruth'].replace(' ', '').replace('-', '').replace('_', '').replace('\n', '')
                candidate = task['soa'].replace(' ', '').replace('-', '').replace('_', '').replace('\n', '')
                merged_df.at[index, f"{method}_strict_eval"] = 1 if gt == candidate else 0
                merged_df.at[index, f"{method}_action_eval"] = json.dumps(check_action_in_groundtruth(row['groundtruth'], task['soa']))
                merged_df.at[index, f"run"] = count
                
                if isinstance(task['soa'], str):
                    if merged_df.at[index, method][-1] != '\n':
                        merged_df.at[index, method] += '\n'
                    merged_df.at[index, method] += f"- ACTION {len(merged_df.at[index, method].split('\n'))}: Task completed?\n"
                
                new_row = row.copy(deep=True)
                new_row[method] = merged_df.at[index, method]
                new_row[f"{method}_strict_eval"] = merged_df.at[index, f"{method}_strict_eval"]
                new_row[f"{method}_action_eval"] = merged_df.at[index, f"{method}_action_eval"]
                new_row['run'] = count
                new_df = new_df._append(new_row, ignore_index=True)
                count += 1
                
           

new_df.to_excel('merged_all_tasks.xlsx', index=False)

with open('not_founds.txt', 'w') as f:
    for method in methods:
        f.write(f"{method}\n")
        for task in not_founds[method]:
            f.write(f"{task}\n")
        f.write('=======\n')
        
with open('mapping.json', 'w') as f:
    json.dump(mapping, f, indent=4)
    
# for method in methods:
#     method_df = method_dfs[method]
#     for index, row in method_df.iterrows():
#         if row['app_name'].lower() + ': ' + row['task_desc'].lower() in mapping:
#             value = mapping[row['app_name'] + ': ' + row['task_desc']]
#             cor_app_name, cor_task_desc, cor_hash = value.split(': ')
#             method_df.at[index, 'app_name'] = cor_app_name
#             method_df.at[index, 'task_desc'] = cor_task_desc
#             method_df.at[index, 'hash'] = cor_hash
            
#             gt = gt_df[(gt_df['app_name'] == cor_app_name) & (gt_df['task_desc'] == cor_task_desc)]
#             method_df.at[index, 'groundtruth'] = gt.iloc[0]['soa']
            
            
            
#     method_df.to_excel(os.path.join('methods', method, 'all_tasks_replaced.xlsx'), index=False)
        
eval_folder = r'evals\evals-visidroid_no_ranking'

app_tasks = method_dfs['visidroid_no_ranking']['app_task'].unique()

visidroid_no_ranking = method_dfs['visidroid_no_ranking']

for app_task in app_tasks:
    tasks = visidroid_no_ranking[visidroid_no_ranking['app_task'] == app_task]
    count=0
    selected_task = tasks[tasks['selected']]
    if len(selected_task) == 0:
        selected_task = tasks.iloc[0]
    else:
        selected_task = selected_task.iloc[0]
    selected_soa = selected_task['soa']
    for index, row in tasks.iterrows():
        app_name = row['app_name']
        hash = row['hash']
        task_desc = row['task_desc']
        visidroid_no_ranking.at[index, 'run'] = count
        
        eval_file = os.path.join(eval_folder, f"{app_name}_{hash}.json")
        if os.path.exists(eval_file):
            soa = row['soa']
            if soa == selected_soa:
                shutil.copyfile(eval_file, os.path.join(eval_folder, f"{app_name}_{hash}_RUN_{count}.json"))
                count += 1

        
