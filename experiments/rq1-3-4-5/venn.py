import json
from venny4py.venny4py import *
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('summary/task_completion.csv')


#dict of sets
sets = {
    'Guardian': set(df[df['guardian']==1]['task']),
    'AutoDroid': set(df[df['autodroid']==1]['task']),
    'VisiDroid': set(df[df['visidroid']==1]['task']),
    'DroidAgent': set(df[df['droidagent']==1]['task']),
}

sets = {f"{k}: {len(v)}": v for k, v in sets.items()}
    
venny4py(sets=sets, out='venn.pdf', )

intersection = get_unique(sets)
dfs = {}
for set_name in intersection:
    print(set_name)
    if ("autodroid" in set_name or "visidroid" in set_name) and "and" not in set_name:
        print(set_name, len(intersection[set_name]))
        if set_name not in dfs:
            dfs[set_name] = pd.DataFrame()
        eval_df = pd.read_excel(f"summary/{set_name}_evals.xlsx")
        other_name = "autodroid" if "visidroid" in set_name else "visidroid"
        if "autodroid" in set_name:
            comparing_df = pd.read_excel(f"summary/visidroid_evals.xlsx")
        else:
            comparing_df = pd.read_excel(f"summary/autodroid_evals.xlsx")
            
        for task in intersection[set_name]:
            app_name = task.split('_')[0]
            hash = task.split('_')[1]
            task_df = eval_df[(eval_df['app_name'] == app_name) & (eval_df['hash'] == hash)]
            # copy the task from the other set, ignore the "app_name", "hash", "task_desc" columns
            other_task_df = comparing_df[(comparing_df['app_name'] == app_name) & (comparing_df['hash'] == hash)]
            other_task_df = other_task_df.drop(columns=['app_name', 'hash', 'task_desc'])
            # rename all columns of other_task_df adding the set_name
            other_task_df.columns = [f"{col}_{other_name}" for col in other_task_df.columns]
            task_df.columns = [f"{col}_{set_name}" for col in task_df.columns]
            # merge the two dataframes
            task_df = task_df.iloc[0]
            other_task_df = other_task_df.iloc[0]
            # concate the columns
            task_df = pd.concat([task_df, other_task_df])
            dfs[set_name] = dfs[set_name]._append(task_df, ignore_index=True) 
            
    # elif ("autodroid" in set_name or "visidroid" in set_name):
    #     set_names = set_name.split(' and ')
    #     for name in set_names:
    #         if name not in dfs:
    #             dfs[name] = pd.DataFrame()
    #         eval_df = pd.read_excel(f"summary/{name}_evals.xlsx")
    #         for task in intersection[name]:
    #             app_name = task.split('_')[0]
    #             hash = task.split('_')[1]
    #             task_df = eval_df[(eval_df['app_name'] == app_name) & (eval_df['hash'] == hash)]
    #             dfs[name] = dfs[name]._append(task_df, ignore_index=True)
            
out_folder = 'analysis'
os.makedirs(out_folder, exist_ok=True)

for set_name in dfs:
    dfs[set_name].to_excel(f"{out_folder}/{set_name}.xlsx", index=False)