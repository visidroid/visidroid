import json
import os
import pandas as pd

def filter_out_actions(soa, evals):
    # return soa, evals
    actions = []
    new_evals = []
    lines = soa.strip().split('\n')
    evals = evals.strip().split('\n')
    
    if len(lines) != len(evals):\
        input(f"Length not equal: {len(lines)} - {len(evals)}")
        
    
    for line, eval in zip(lines, evals):
        if not "ACTION" in line or 'scroll' in line or 'BACK' in line or "Open the app again" in line:
            with open("filtered_out.txt", 'a') as f:
                f.write(f"{line} - {eval}\n")
            continue
        line = line.lower()
        actions.append(line)
        new_evals.append(eval)
    return '\n'.join(actions), '\n'.join(new_evals)

def prefix_complete(evals, gt):
    # count the first Trues
    count = 0
    evals = evals.strip().split('\n')
    gt = gt.strip().split('\n')
    for eval in evals:
        if eval == 'True':
            count += 1
        else:
            break
    return count/len(evals)

# ----- Main -----

# methods = ['autodroid', 'guardian', 'visidroid', 'droidagent']
methods = ['guardian','droidagent', 'autodroid',  'visidroid',  'visidroid_no_mem', 'visidroid_no_vision',]
        #    'visdroid']
all_results = {}
task_completion_df = pd.DataFrame(columns=['task']+methods)
dfs = {}
for method in methods:
    eval_folder = f"evals/evals-{method}"
    files = os.listdir(eval_folder)

    df = pd.DataFrame(columns=['app_name', 'task_desc', 'hash', 'soa', 'evals', 'task_completed', 'all_correct'])

    for file in files:
        with open(os.path.join(eval_folder, file)) as f:
            data = json.load(f)
            actions = data['actions']
            evals = data['evals']
            
            app_name = data['app_name']
            task_desc = data['task_desc']
            hash = data['hash']
            task_completed = evals[-1]
            
            all_correct = all(evals)
            
            row = {
                'app_name': app_name,
                'task_desc': task_desc,
                'hash': hash,
                'soa': '\n'.join(actions),
                'evals': '\n'.join([str(eval) for eval in evals]),
                'task_completed': task_completed,
                'all_correct': all_correct
            }
            
            df = df._append(row, ignore_index=True)
    print("Length in the beginning: ", len(df))
    
    all_tasks = pd.read_excel("merged_all_tasks.xlsx")
    for index, row in all_tasks.iterrows():
        hash = row['hash']
        app_name = row['app_name']
        if len(df[(df['app_name'] == app_name) & (df['hash'] == hash)]) > 0:
            continue
        # if hash in df['hash'].values:
        #     continue
        app_name = row['app_name']
        task_desc = row['task_desc']
        soa = row[method] if not pd.isna(row[method]) else ""
        
        all_correct = True if row[f'{method}_strict_eval'] == 1 else False 
        
        
        new_row = {
            'app_name': app_name,
            'task_desc': task_desc,
            'hash': hash,
            'soa': soa,
            'evals': "True\n"*soa.count('\n'),
            'task_completed': True,
            'all_correct': all_correct
        }
        
        df = df._append(new_row, ignore_index=True)
        
    print("Length after adding missing tasks: ", len(df))
    
    # add groundtruth to the dataframe
    for index, row in all_tasks.iterrows():
        hash = row['hash']
        app_name = row['app_name']
        
        candidate_row = df[(df['app_name'] == app_name) & (df['hash'] == hash)]
        if len(candidate_row) == 1:
            df.loc[candidate_row.index, 'groundtruth'] = row['groundtruth']



    for index, row in df.iterrows():
        filtered_soa, filtered_evals = filter_out_actions(row['soa'], row['evals'])
        df.loc[index, 'soa'] = filtered_soa
        df.loc[index, 'evals'] = filtered_evals
        
        last_action_eval = row['evals'].split('\n')[-2] if len(row['evals'].split('\n')) > 1 else False
        task_completed = row['task_completed']
        app_name_hash = row['app_name'] + "_" + row['hash']
        if app_name_hash not in task_completion_df['task'].values:
            task_completion_df.loc[index, 'task'] = row['app_name'] + "_" + row['hash']
        if last_action_eval == 'True' and task_completed:
            df.loc[index, 'task_completion'] = True
            # add to task_completion_df
            # find the index of the task in task_completion_df
            task_completion_df.loc[task_completion_df['task'] == app_name_hash, method] = 1
        else:
            df.loc[index, 'task_completion'] = False
            task_completion_df.loc[task_completion_df['task'] == app_name_hash, method] = 0
            
        if last_action_eval == 'True' and not task_completed:
            df.loc[index, 'not_done_but_end'] = True
        else:
            df.loc[index, 'not_done_but_end'] = False


    # for each line calculate the number of correct actions and the number of actions
    df['correct_actions'] = df['evals'].apply(lambda x: x.count('True'))
    df['total_actions'] = df['evals'].apply(lambda x: len(x.split('\n')))
    df['precision'] = df['correct_actions'] / df['total_actions']
    df['prefix_complete'] = df.apply(lambda x: prefix_complete(x['evals'], x['groundtruth']), axis=1)

    total_tasks = 150
    result = {
        'total_tasks': 150,
        'total_exact_match_tasks': len(df[df['all_correct'] == True]),
        'exact_match_percentage': len(df[df['all_correct'] == True]) / total_tasks,
        'average_prefix_match': df['prefix_complete'].mean(),
        'total_correct_actions': int(df['correct_actions'].sum()),
        'total_actions': int(df['total_actions'].sum()),
        'macro_average_precision': df['precision'].mean(),
        'micro_average_precision': df['correct_actions'].sum() / df['total_actions'].sum(),
        'task_achieved': len(df[df['task_completed'] == True]),
        'total_tasks_completed': len(df[df['task_completion'] == True]),
        'task_completion_percentage': len(df[df['task_completion'] == True]) / total_tasks,
        'task_not_done_but_end': len(df[df['not_done_but_end'] == True]),
    }
    df.sort_values(by=['app_name', 'task_desc'], inplace=True)
    df.to_excel(f"summary/{method}_evals.xlsx", index=False)
    with open(f"summary/{method}_result.json", 'w') as f:
        json.dump(result, f, indent=4) 
        
    all_results[method] = result
    dfs[method] = df
    
result_df = pd.DataFrame(all_results)
# if cell is float, round it to 2 decimal places
result_df = result_df.applymap(lambda x: round(x*100, 1) if isinstance(x, float) and x < 1 else x)
result_df.to_csv("summary/results.csv")

rename = {
    "total_tasks": "#Tasks",
    "total_exact_match_tasks": "#Exact-match tasks",
    "total_tasks_completed": "#Completed tasks",
    "task_achieved": "#Tasks achieved",
    "task_not_done_but_end": "#Tasks not done but ended",
    "exact_match_percentage": "Exact-match(%)",
    "average_prefix_match": "Prefix-match(%)",
    "macro_average_precision": "Precision(%)",
    "task_completion_percentage": "Task completion(%)",
}

format_result_df = pd.DataFrame()
for key, value in rename.items():
    format_result_df[value] = result_df.loc[key]
    
# rows in order: ["guardian",  "droidagent","autodroid", "visidroid",]
format_result_df = format_result_df.T
format_result_df = format_result_df[methods]
# rename columns
rename = {
    "guardian": "Guardian",
    "droidagent": "DroidAgent",
    "autodroid": "AutoDroid",
    "visidroid": "VisiDroid",
    "visidroid_no_mem": "VisiDroid-m",
    "visidroid_no_vision": "VisiDroid-v",
}
format_result_df = format_result_df.rename(columns=rename)
for i, row in format_result_df.iterrows():
    # cell under col VisiDroid-m and VisiDroid-v, format as {value} ({visidroid - value})
    # get row index
    if "#" in i:
        m_gap = int(row['VisiDroid-m'] - row['VisiDroid'])
        m_gap = f"+{m_gap}" if m_gap > 0 else m_gap
        v_gap = int(row['VisiDroid-v'] - row['VisiDroid'])
        v_gap = f"+{v_gap}" if v_gap > 0 else v_gap
        format_result_df.loc[i, "VisiDroid-m"] = f"{int(row['VisiDroid-m'])} ({m_gap})"
        format_result_df.loc[i, "VisiDroid-v"] = f"{int(row['VisiDroid-v'])} ({v_gap})"
    else:
        # format the same but round to 1 decimal place
        format_result_df.loc[i, "VisiDroid-m"] = f"{round(row['VisiDroid-m'], 1)} ({round(row['VisiDroid-m']-row['VisiDroid'], 1)})"
        format_result_df.loc[i, "VisiDroid-v"] = f"{round(row['VisiDroid-v'], 1)} ({round(row['VisiDroid-v']-row['VisiDroid'], 1)})"
    
format_result_df.to_csv("summary/formatted_results.csv")
    
task_completion_df.to_csv("summary/task_completion.csv", index=False)