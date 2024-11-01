import json
from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
methods = ['autodroid', 'visidroid', 'guardian', 'droidagent']
precision_by_step_dict = {'groundtruth': {}}
added = False
for method in methods:
    if method not in precision_by_step_dict:
        precision_by_step_dict[method] = {}
        
    eval_file = f"summary/{method}_evals.xlsx"
    df = pd.read_excel(eval_file)
    # filter where task_completion is True
    evals = df['evals']
    evals = evals.apply(lambda x: x.split('\n') if isinstance(x, str) else [])
    
    groundtruth = df['groundtruth']
    len_gts = groundtruth.apply(lambda x: len(x.split('\n')) if isinstance(x, str) else 0)
    
    if not added:
        for len_gt in len_gts:
            if len_gt not in precision_by_step_dict['groundtruth']:
                precision_by_step_dict['groundtruth'][len_gt] = 0
            precision_by_step_dict['groundtruth'][len_gt] += 1
    
    added = True
    
    task_completions = df['all_correct']    
    for len_gt, task_completions in zip(len_gts, task_completions):
        if len_gt not in precision_by_step_dict[method]:
            precision_by_step_dict[method][len_gt] = 0
        if task_completions:
            precision_by_step_dict[method][len_gt] += 1
        
labels_dict = {}
methods = ['VisiDroid', 'DroidAgent', 'AutoDroid', ]

new_precision_by_step_dict = {
    "AutoDroid": precision_by_step_dict["autodroid"],
    "VisiDroid": precision_by_step_dict["visidroid"],
    # "Guardian": precision_by_step_dict["guardian"],
    "DroidAgent": precision_by_step_dict["droidagent"],
    "groundtruth": precision_by_step_dict["groundtruth"]
}

precision_by_step_dict = new_precision_by_step_dict

for method in methods:
    precision_by_step_dict[method] = dict(sorted(precision_by_step_dict[method].items()))

    if method not in labels_dict:
        labels_dict[method] = []
    for key in precision_by_step_dict[method]:
        print(key, precision_by_step_dict[method][key], precision_by_step_dict['groundtruth'][key])
        labels_dict[method].append(f"{precision_by_step_dict[method][key]}/{precision_by_step_dict['groundtruth'][key]}")
        precision_by_step_dict[method][key] /= precision_by_step_dict['groundtruth'][key]
    # sort the dictionary by key
precision_by_step_dict['groundtruth'] = dict(sorted(precision_by_step_dict['groundtruth'].items()))
with open("summary/precision_by_step.json", 'w') as f:
    json.dump(precision_by_step_dict, f)
    
# rename autodroid to AutoDroid, visidroid to VisiDroid


sns.set(style="whitegrid", palette="bright", font_scale=2)  # Use a soft color palette and increase font scale for readability

plt.figure(figsize=(10, 7))  # Adjust figure size for better layout

# Loop over methods to plot each line with discrete markers
for method in methods:
    sns.lineplot(x=list(range(len(precision_by_step_dict[method].keys()))),  # Set x as range to make discrete spacing
                 y=list(precision_by_step_dict[method].values()), 
                 label=method, linewidth=4, marker='o')
    # for i, label in enumerate(labels_dict[method]):
    #     plt.text(i, list(precision_by_step_dict[method].values())[i], label, fontsize=16, ha='center', va='bottom')
# Set labels and title with adjusted font sizes
plt.xlabel('Task Length', fontsize=25, labelpad=10)
plt.ylabel('%Exact-match', fontsize=25, labelpad=10)

# Set the x-ticks to the actual step labels and evenly space them
plt.xticks(ticks=range(len(precision_by_step_dict["AutoDroid"].keys())), 
           labels=list(precision_by_step_dict["AutoDroid"].keys()), fontsize=25)
plt.yticks(fontsize=25)

# Customize legend
plt.legend(fontsize=25, title_fontsize=25)

# Tight layout and save
plt.tight_layout()
plt.savefig("summary/precision_by_step.pdf", bbox_inches='tight')

# plt.show()
