# visidroid\hai-visidroid-results-with-score.xlsx

import os
import pandas as pd

def re_index(soa):
    soa = soa.strip().split('\n')
    remove_indices = []
    for i in range(len(soa)):
        if "button to navigate back" in soa[i]:
            remove_indices.append(i)
        elif "scrolled down on a scrollable" in soa[i]:
            remove_indices.append(i)
        elif "Open the app again" in soa[i]:
            remove_indices.append(i)
        soa[i] = soa[i].replace('Jade Green ', '').replace('content_desc', 'content-desc')
    
    new_soa = [soa[i] for i in range(len(soa)) if i not in remove_indices ]
    soa = new_soa
    for i in range(len(soa)):
        # split - ACTION {new_index}: {action}
        after = soa[i].split(': ', 1)[1]
        soa[i] = "- ACTION " + str(i+1) + ": " + after
        
    return "\n".join(soa)    
    

file = r'methods\visidroid_no_vision\results-with-score.xlsx'
folder = os.path.dirname(file)

visidroid = pd.read_excel(file)
visidroid = visidroid[visidroid['selected']]
visidroid = visidroid.drop(columns=['selected', 'related_score'])

remove_indices = []
for index, row in visidroid.iterrows():
    soa = row['soa']
    
    soa = re_index(soa)
    
    visidroid.at[index, 'soa'] = soa
    
# sort by app_name then task_desc
visidroid = visidroid.sort_values(by=['app_name', 'task_desc'])
    
visidroid.to_excel(f'{folder}/all_tasks.xlsx', index=False)
# all apps
apps = visidroid['app_name'].unique()
with open(f'{folder}/apps.txt', 'w') as f:
    for app in apps:
        f.write(app + '\n')