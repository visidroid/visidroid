import json
import os 
import pandas as pd

gt_file = 'autodroid/result_analysis copy.json'

gt = json.load(open(gt_file))

all_tasks = pd.DataFrame()

for app in gt:
    for hashed_task in gt[app]:
        task = gt[app][hashed_task]
        task_desc = task['task']
        n_actions = task['step_num']
        
        actions = task['profile']
        my_actions = []
        nl_actions = ""
        for index, action in enumerate(actions):
            label = action['answer']
            label = [label[0], label[2]]
            action_type = ""
            
            if label[1] != 'N/A':
                action_type = "set_text"
            else:
                action_type = "click"
            
            id = label[0]
            states = action['state'].split('>\n')
            if id != -1:
                print(f"Task: {task_desc}, id: {id}")
                if id >= len(states):
                    continue
                target_element = states[id]
                text, _text = None, None
                if 'text=' in target_element:
                    text = target_element.split('text=')[1]
                    quote = text[0]
                    # find the right quote
                    right_quote = -1
                    for i in range(1, len(text)):
                        if text[i] == quote:
                            right_quote = i
                            break
                    text = text[1:right_quote]
                    with open('text.txt', 'a') as f:
                        f.write(text + '\n')
                elif '><' not in target_element:
                    # get the text between > and <
                    _text = target_element.split('>')[1].split('<')[0]
                else:
                    text = ""
                target_element_obj = {
                    "action": action_type,
                    "text": _text,
                    "content-desc": text,
                    'input_text': None if action_type != 'set_text' else label[1]
                }
                
                nl_action = f'- ACTION {index + 1}: '
                if action_type == 'click':
                    nl_action += 'touched on a button that has'
                else:
                    nl_action += 'filled a focused textfield that has'
                    
                if text is not None:
                    nl_action += f' content-desc "{text}"'
                if _text is not None:
                    nl_action += f' text "{_text}"'
                    
                if action_type == 'set_text':
                    nl_action += f' with the text "{label[1]}"'
                
                my_actions.append(target_element_obj)
                nl_actions += nl_action + '\n'
                
        all_tasks = all_tasks._append({
            'app_name': app,
            'task_desc': task_desc,
            'hash': hashed_task,
            'n_actions': n_actions,
            'actions': my_actions, 
            'soa': nl_actions
        }, ignore_index=True)
        
# sort by app_name then task_desc
all_tasks = all_tasks.sort_values(by=['app_name', 'task_desc']) 

os.chdir('autodroid')
all_tasks.to_excel('all_tasks.xlsx')