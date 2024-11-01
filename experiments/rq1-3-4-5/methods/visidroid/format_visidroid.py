# visidroid\hai-visidroid-results-with-score.xlsx

import pandas as pd

file = r'methods\visidroid\hai-visidroid-results-with-score - Copy.xlsx'
visidroid = pd.read_excel(file)
visidroid = visidroid[visidroid['selected']]
visidroid = visidroid.drop(columns=['selected', 'related_score'])

for index, row in visidroid.iterrows():
    visidroid.at[index, 'soa'] = row['soa'].replace('Jade Green ', '').replace('content_desc', 'content-desc')
    
# sort by app_name then task_desc
visidroid = visidroid.sort_values(by=['app_name', 'task_desc'])
    
visidroid.to_excel(r'methods\visidroid/all_tasks_.xlsx', index=False)
# all apps
apps = visidroid['app_name'].unique()
with open(r'methods\visidroid/apps.txt', 'w') as f:
    for app in apps:
        f.write(app + '\n')