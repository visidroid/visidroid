import json
import os
import tkinter as tk
from tkinter import ttk
import pandas as pd

comparing_method = 'visidroid_no_ranking'
eval_dir = f"evals/evals-{comparing_method}"

# Function to handle input validation and focus navigation
def validate_input(event, entry, gt_index, candidate_index):
    value = entry.get().lower()
    if value in ('t', 'f'):
        print(f'GT Action {gt_index + 1} is {"Correct" if value == "t" else "Incorrect"}')
        print(f'Candidate Action {candidate_index + 1} is {"Correct" if value == "t" else "Incorrect"}')
    else:
        entry.delete(0, tk.END)  # Clear invalid input

def focus_next_widget(event):
    next_widget = event.widget.tk_focusNext()
    while next_widget and not isinstance(next_widget, (tk.Entry, ttk.Entry)):  # Loop until an input widget is found
        next_widget = next_widget.tk_focusNext()
        canvas.yview_moveto(canvas.yview()[1])
    if next_widget:
        next_widget.focus()
        next_widget.selection_range(0, tk.END)
    return "break"

def focus_prev_widget(event):
    prev_widget = event.widget.tk_focusPrev()
    while prev_widget and not isinstance(prev_widget, (tk.Entry, ttk.Entry)):  # Loop until an input widget is found
        prev_widget = prev_widget.tk_focusPrev()
        canvas.yview_moveto(canvas.yview()[0])
    if prev_widget:
        prev_widget.focus()
        prev_widget.selection_range(0, tk.END)
    return "break"


def clear_display(frame):
    for widget in frame.winfo_children():
        widget.destroy()
        
def fill_all_entries_with_f(can_entries):
    for entry in can_entries:
        # if null, fill with f
        if entry.get() == '':
            entry.insert(0, 'f')
    

# Navigation functions
def show_previous():
    global current_index
    if current_index > 0:
        current_index -= 1
        update_display()

def show_next():
    global current_index
    save = save_results()
    print(f"Saved: {save}")
    if save == -1:
        return
        
    if current_index < len(df) - 1:
        current_index += 1
        update_display()
        
def update_display():
    global df, current_index, candidate_entries
    
    gt_actions = df.iloc[current_index]['groundtruth'].strip().split('\n')
    candidate_actions = df.iloc[current_index][comparing_method].strip().split('\n')
    original_gt_size = len(candidate_actions)
    action_evals = df.iloc[current_index][f"{comparing_method}_action_eval"]
    action_evals = json.loads(action_evals) if not pd.isna(action_evals) else []
    
    # if gt_actions and candidate_actions and action_evals are not the same length, pad with empty strings
    max_len = max(len(gt_actions), len(candidate_actions), len(action_evals))
    for arr in [gt_actions, candidate_actions, action_evals]:
        if len(arr) < max_len:
            arr += [''] * (max_len - len(arr))
    # print last can action
    print(candidate_actions[-1])

    # Create a frame for the actions and inputs
    clear_display(frame)
    
    # a big title showing current app and task, align center
    title = tk.Label(frame, text=f"{df.iloc[current_index]['app_name']} - {df.iloc[current_index]['task_desc']} - {df.iloc[current_index]['run']}", 
                     font=("Arial", 16), anchor="center", fg="blue", wraplength=800)
    title.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    
    progress = tk.Label(frame, text=f"Progress: {current_index + 1}/{len(df)}", font=("Arial", 12), anchor="center", bg="red", wraplength=800)
    progress.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
    
    error = tk.Label(frame, text="", font=("Arial", 12), anchor="w", fg="red", wraplength=800)
    error.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
    candidate_entries.clear()
    evals = load_results(df.iloc[current_index]['app_name'], df.iloc[current_index]['hash'], df.iloc[current_index]['run'], df.iloc[current_index][comparing_method].strip().split('\n'))
    if evals == "-1":
        show_next()
    print(len(list(zip(gt_actions, candidate_actions, action_evals))))
    for i, (gt_action, candidate_action, action_eval) in enumerate(zip(gt_actions, candidate_actions, action_evals)):
        # Ground Truth actions
        gt_label = tk.Label(frame, text=gt_action, anchor="w", wraplength=600, font=("Arial", 15))
        gt_label.grid(row=i+4, column=0, padx=10, pady=5, sticky="w")

        # if action eval is true, color text is green, else red
        color = "green" if action_eval else "red"
        # Candidate actions
        candidate_label = tk.Label(frame, text=candidate_action, anchor="w", wraplength=600, font=("Arial", 15), fg=color)
        candidate_label.grid(row=i+4, column=1, padx=10, pady=5, sticky="w")

        if i >= original_gt_size: # Skip the input for extra candidate actions
            continue
        # Input for Candidate action
        candidate_entry = tk.Entry(frame)
        candidate_entry.grid(row=i+4, column=3, padx=10, pady=5)
        candidate_entry.bind("<Return>", lambda e: show_next())
        candidate_entry.bind("<Down>", focus_next_widget)
        candidate_entry.bind("<Up>", focus_prev_widget)
        # left and right arrow key to navigate between entries
        candidate_entry.bind("<Right>", lambda e: show_next())
        candidate_entry.bind("<Left>", lambda e: show_previous())
        # bind control + f to fill all entries with 'f'
        candidate_entry.bind("<Control-f>", lambda e: fill_all_entries_with_f(candidate_entries))
        
        
        if action_eval:
            candidate_entry.delete(0, tk.END)
            candidate_entry.insert(0, 't')
        
        if evals is not None and i < len(evals):
            candidate_entry.delete(0, tk.END)
            candidate_entry.insert(0, 't' if evals[i] else 'f')
        
        candidate_entries.append(candidate_entry)



    # focus on the first entry
    if len(candidate_entries) > 0:
        candidate_entries[0].focus()
    # Add navigation buttons
    prev_button = tk.Button(frame, text="Previous", command=show_previous)
    prev_button.grid(row=i+100
                     , column=0, padx=10, pady=10, sticky="w")

    next_button = tk.Button(frame, text="Next", command=show_next)
    next_button.grid(row=i+100
                     , column=2, padx=10, pady=10, sticky="e")


    # Configure the canvas scrolling region
    frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

def save_results():
    global df, candidate_entries
    app_name = df.iloc[current_index]['app_name']
    task_desc = df.iloc[current_index]['task_desc']
    hash = df.iloc[current_index]['hash']
    run = df.iloc[current_index]['run']
    actions = df.iloc[current_index][comparing_method].split('\n')
    results = {
        'app_name': app_name,
        'task_desc': task_desc,
        'hash': hash,
        'actions': actions,
        'evals': [],
        'end_correctly': False,
    }
    
    for i, entry in enumerate(candidate_entries):
        value = entry.get().lower()
        if value in ('t', 'f'):
            value = True if value == 't' else False
            results['evals'].append(value)
        else:
            entry.delete(0, tk.END)
            return -1
    
    if not os.path.exists(eval_dir):
        os.mkdir(eval_dir)
    with open(os.path.join(eval_dir, f"{app_name}_{hash}_RUN_{run}.json"), 'w') as f:
        json.dump(results, f, indent=4)
        
def load_results(app_name, hash, run, soa):
    if not os.path.exists(eval_dir):
        return None
    if not os.path.exists(os.path.join(eval_dir, f"{app_name}_{hash}_RUN_{run}.json")):
        for i in range(3):
            if i == run:
                continue
            if os.path.exists(os.path.join(eval_dir, f"{app_name}_{hash}_RUN_{i}.json")):
                with open(os.path.join(eval_dir, f"{app_name}_{hash}_RUN_{i}.json"), 'r') as f:
                    content = json.load(f)
                    if content['actions'] == soa:
                        # copy the file
                        with open(os.path.join(eval_dir, f"{app_name}_{hash}_RUN_{run}.json"), 'w') as f:
                            json.dump(content, f, indent=4)
                            return -1
        return None

    with open(os.path.join(eval_dir, f"{app_name}_{hash}_RUN_{run}.json"), 'r') as f:
        return json.load(f)['evals']
    

file = "merged_all_tasks.xlsx"
df = pd.read_excel(file)
# filter df where method_strict_eval is False
df = df[df[f"{comparing_method}_strict_eval"] == False]
df["evaluated"] = df.apply(lambda x: os.path.exists(os.path.join(eval_dir, f"{x['app_name']}_{x['hash']}_RUN_{x['run']}.json")), axis=1)

if len(df) == 0:
    print("All tasks have been evaluated")
    exit()





root = tk.Tk()
root.title("Action Evaluation (GT vs Candidate)")
# set fullscreen
root.state('zoomed')

current_index = 49



# Create a canvas
canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor="center")



# Scrollbar for the canvas
scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.config(yscrollcommand=scrollbar.set)

# Create headers
gt_header = tk.Label(frame, text="Ground Truth Actions", font=("Arial", 14), anchor="w")
gt_header.grid(row=0, column=0, padx=10, pady=10, sticky="w")
candidate_header = tk.Label(frame, text="Candidate Actions", font=("Arial", 14), anchor="w")
candidate_header.grid(row=0, column=2, padx=10, pady=10, sticky="w")

candidate_entries = []

update_display()

# Run the main loop
root.mainloop()
