import json
import csv
import os
import argparse

#### py .\make_csv_report.py --app_name "Voice Recorder" --type train #######
    
def make_csv_report(result_dir, app_name, type):
    report_json_file = os.path.join(result_dir, f"{app_name}_{type}.json")
    print(report_json_file)

    if os.path.exists(report_json_file):
        with open(report_json_file, 'r') as f:
            json_data = json.load(f)
    else:
        print("Invalid input app name")
    # print(json_data)
    
    keys = set()
    for task in json_data.values():
        for entry in task:
            keys.update(entry.keys())


    keys.add("task")

    # Writing data to CSV
    with open('tasks.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Task', 'Summary', 'Task Result', 'Steps Count' ,'History Action', 'Optimization', 'Reflections',])
        for task, entries in json_data.items():
            for entry in entries:
                history_action = entry.get('history_action', '')
                num_steps = len(history_action.split('\n')) if history_action else 0

                writer.writerow([task, entry['summary'], entry.get('task_result', ''), num_steps, history_action, entry['optimization'], entry['reflections'], ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make GUI testing scripts from experiment data')
    parser.add_argument('--result_dir', type=str, help='Result directory', default="../evaluation/data_new")
    parser.add_argument('--app_name', type=str, help='App name (Notes)')
    parser.add_argument('--type', type=str, help='Training or Evaluate type')
    args = parser.parse_args()

    result_dir = args.result_dir
    app_name = args.app_name
    type = args.type
    print(type)
    if not (type != "train" or type != "evaluate"):
        print("Type must be 'train' or 'evaluate'")
        exit(1)
    
    make_csv_report(result_dir=result_dir, app_name=app_name, type=type)