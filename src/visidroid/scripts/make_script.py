import sys
import os
import time
import json
import glob
import shutil
import argparse

import pandas as pd
from datetime import datetime

# python make_script.py --project VoiceRecorder --package_name com.simplemobiletools.voicerecorder --result_dir ../evaluation/data_new/Contacts_26/training_phase/train

def get_widget_identifier(action_data):
    text = None
    content_desc = None
    resource_id = None
    bounds = None

    selector_str = 'd('

    if action_data['target_widget_text'] is not None and len(action_data['target_widget_text']) > 0:
        text = action_data['target_widget_text'].removesuffix('[...]').split('"')[0].split('\n')[0]
        selector_str += f'textStartsWith="{text}"'

    if action_data['target_widget_content_description'] is not None and len(action_data['target_widget_content_description']) > 0:
        content_desc = action_data['target_widget_content_description']
        if selector_str != 'd(':
            selector_str += ', '
        selector_str += f'descriptionMatches=".*{content_desc}"'

    if action_data['target_widget_resource_id'] is not None and len(action_data['target_widget_resource_id']) > 0:
        resource_id = action_data['target_widget_resource_id']
        if selector_str != 'd(':
            selector_str += ', '
        selector_str += f'resourceIdMatches=".*{resource_id}"'

    if selector_str == 'd(' and action_data['target_widget_bounds'] is not None:
    # FIXME: position-based replay is very unstable (will not work with different screen size)
        bounds = action_data['target_widget_bounds']
        center_x = (bounds[0][0] + bounds[1][0]) // 2
        center_y = (bounds[0][1] + bounds[1][1]) // 2
        return None, (center_x, center_y)

    return selector_str + ')', None

def get_selector_appium(action_data, event_view):
    text = None
    content_desc = None
    resource_id = None
    bounds = None
#     # device.driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@resource-id="com.simplemobiletools.notes.pro:id/new_note" and @text="" and @content-desc="Create a new note"]").click()
#     time.sleep(1)
#     element = device.driver.find_element(
#         AppiumBy.XPATH, "//android.widget.ImageButton[@resource-id='com.simplemobiletools.contacts.pro:id/fragment_fab' and @text='' and @content-desc='Create new contact']")
#     element.click()
    selector_str = f'//{event_view['class']}['

    if action_data['target_widget_text'] is not None and len(action_data['target_widget_text']) > 0:
        text = action_data['target_widget_text'].removesuffix('[...]').split('"')[0].split('\n')[0]
        selector_str += f"@text='{text}' and "

    if action_data['target_widget_content_description'] is not None and len(action_data['target_widget_content_description']) > 0:
        content_desc = action_data['target_widget_content_description']

        selector_str += f"@content-desc='{content_desc}' and "

    if action_data['target_widget_resource_id'] is not None and len(action_data['target_widget_resource_id']) > 0:
        resource_id = action_data['target_widget_resource_id']
        selector_str += f"@resource-id='{resource_id}'"
    
            
    if selector_str == f'//{event_view['class']}' and action_data['target_widget_bounds'] is not None:
    # FIXME: position-based replay is very unstable (will not work with different screen size)
        bounds = action_data['target_widget_bounds']
        center_x = (bounds[0][0] + bounds[1][0]) // 2
        center_y = (bounds[0][1] + bounds[1][1]) // 2
        return None, (center_x, center_y)
        

    selector_str = selector_str.rstrip(" and ")
    selector_str += "]"
    script = f'driver.find_element(AppiumBy.XPATH, "{selector_str}")'
    
    return script, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make GUI testing scripts from experiment data')
    parser.add_argument('--result_dir', type=str, help='Result directory')
    parser.add_argument('--package_name', type=str, help='App package name (ex. org.odk.collect.android)')
    parser.add_argument('--project', type=str, help='Project name')
    args = parser.parse_args()

    result_path = args.result_dir
    target_project = args.project
    package_name = args.package_name

    state_str_to_screenshot_path = {}
    for state_file in glob.glob(os.path.join(result_path, 'states', '*.json')):
        with open(state_file, 'r') as f:
            state_data = json.load(f)
            state_str = state_data['state_str']
            screenshot_path = 'file://' + str(os.path.abspath(os.path.join(result_path, 'states', f'screen_{state_data["tag"]}.png')))
            state_str_to_screenshot_path[state_str] = screenshot_path
    exp_data_file = os.path.join(result_path, 'exp_data.json')

    with open(exp_data_file, 'r') as f:
        exp_data = json.load(f)

    task_results = list(exp_data['task_results'].items())

    if len(task_results) == 0:
        print('No task results...')
        exit(0)
    
    if os.path.exists(f'../gen_tests/{target_project}/'):
        shutil.rmtree(f'../gen_tests/{target_project}/')
    os.makedirs(f'../gen_tests/{target_project}/')

    # state_files = sorted(glob.glob(os.path.join(result_path, 'states', '*.json')))
    # with open(state_files[0]) as f:
    #     first_state = json.load(f)

    # original_width = first_state['width']
    # original_height = first_state['height']
    
    script_content = f'''
import sys
import time
import uiautomator2 as u2
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.common.touch_action import TouchAction
from device import Device
from config import *

def wait(seconds=3):
    for i in range(0, seconds):
        print("wait 1 second ..")
        time.sleep(1)

def wait_until_activity(d, activity_name, max_wait=30):
    for i in range(0, max_wait):
        current_app = d.app_current()
        if current_app['package'] == "{package_name}" and activity_name in current_app['activity']:
            break
        time.sleep(1)
    
    # if the target activity is not launched, raise exception
    current_app = d.app_current()
    if current_app['package'] != "{package_name}" or activity_name not in current_app['activity']:
        raise Exception(f"Action precondition cannot be satisfied: %s is not launched" % activity_name)

def go_back_until_inside_app(d, max_backtrack=10):
    for i in range(0, max_backtrack):
        current_app = d.app_current()
        if current_app['package'] == "{package_name}":
            break
        d.press("back")
    
    raise Exception(f"Backtrack failed: {package_name} is not launched")

def setup_device(platform, platformVersion, deviceName, appPackage, appActivity):
        device = Device(
            platform=platform,
            platformVersion=platformVersion,
            deviceName=deviceName,
            appPackage=appPackage,
            appActivity=appActivity,
        )
        return device

config = AppConfig()
config.load_from_env()
device = setup_device(
        config.platform,
        config.platformVersion,
        config.deviceName,
        '{package_name}',
        '{package_name}.activities.MainActivity')
device.connect()
driver = device.driver
wait()

'''

    for i, (task, task_result) in enumerate(task_results):
        script_content += f'''"""
{i+1}. {task}
"""
'''
        for entry in task_result['task_execution_history']:
            if entry['type'] == 'ACTION':
                # script_content += f'''wait_until_activity(d, "{entry["page"]}")'''
                # script_content += '\n'
                # print(entry['action_data']['action_type'])
                # print(entry['events'][0]['event']['view']['class'])
                # case 1: user action
                script_content += '''
try:'''
                if entry['action_data'] is not None:
                    # POSITION is X and Y of the bounds
                    # selector_str, position = get_widget_identifier(entry['action_data'], entry['events']) 
                    if not (entry['action_data']['action_type'] == 'wait' or entry['action_data']['action_type'] == 'key'):
                        selector_str, position = get_selector_appium(entry['action_data'], entry['events'][0]['event']['view'])
                    ## TOUCH    
                    if entry['action_data']['action_type'] == 'touch':
                        if selector_str is None:
                            script_content += f'''
    action = TouchAction(driver)
    action.tap({position[0]}, {position[1]}).perform()'''
                        else:
                            script_content += f'''
    {selector_str}.click()'''
                    ## LONG TOUCH  
                    elif entry['action_data']['action_type'] == 'long_touch':
                        if selector_str is None:
                            script_content += f'''
    action = TouchAction(driver)
    action.long_press({position[0]}, {position[1]}).perform()'''
                        else:
                            script_content += f'''
    elem = {selector_str}'''
                            script_content += f'''
    action = TouchAction(driver)
    action.long_press(elem).perform()'''
                            
                    ## SET TEXT
                    elif entry['action_data']['action_type'] == 'set_text':
                        script_content += f'''
    {selector_str}.send_keys("{entry['action_data']['text'].replace('"', '')}")'''
                    ## SCROLL
                    elif entry['action_data']['action_type'] == 'scroll':
                        script_content += f'''
    deviceSize = driver.get_window_size()
    width = deviceSize['width']
    height = deviceSize['height']
    start_x, start_y = width/2, height/2
    end_x, end_y = width/2, height/2
    duration = 500'''
                        if entry['action_data']['direction'] == 'UP':
                            script_content += f'''
    start_y -= height * 2 / 5
    end_y += height * 2 / 5'''
                        elif entry['action_data']['direction'] == 'DOWN':
                            script_content += f'''
    start_y += height * 2 / 5
    end_y -= height * 2 / 5'''
                        elif entry['action_data']['direction'] == 'LEFT':
                            script_content += f'''
    start_x -= width * 2 / 5
    end_x += width * 2 / 5'''
                        elif entry['action_data']['direction'] == 'RIGHT':
                            script_content += f'''
    start_x += width * 2 / 5
    end_x -= width * 2 / 5'''
                        
                        script_content += f'''
    driver.swipe(start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y, duration=duration)'''
                    ## BACK  
                    elif entry['action_data']['action_type'] == 'key':
                        if entry['action_data']['name'] == 'BACK':
                            script_content += f'''
    driver.back()'''

                    # case 2: wait action (wait until activity is launched, etc.)
                    elif entry['action_data']['action_type'] == 'wait':
                        script_content += f'''
    wait()'''

                # case 3: recovery action (send open intent, press back multiple times, etc.)
                else:
                    if entry['description'].startswith('Open the app again'):
                        script_content += f'''
    driver.back()'''
                    elif entry['description'].startswith('Press the back button'):
                        script_content += f'''
    driver.back()'''

                cleaned_description = entry['description'].replace('"', "'").replace('\n', ' ').encode('ascii', 'ignore').decode('ascii')
                script_content += f'''
    print("{cleaned_description}: SUCCESS")
    wait()'''
                script_content += f'''
except Exception as e:
    print("{cleaned_description}: FAILED")'''
            elif entry['type'] == 'OBSERVATION':
                script_content += f'''\n
# Expected behaviour: {entry['description']}'''
                script_content += '\n\n'
script_content += '''
screenshot_path = "./script_state.png"
driver.get_screenshot_as_file(screenshot_path)
'''

src_dir = "./configs"

for item in os.listdir(src_dir):
    src_item = os.path.join(src_dir, item)
    dest_item = os.path.join('../gen_tests', target_project, item)
    
    # Check if the item is a file or directory and copy accordingly
    if os.path.isdir(src_item):
        # Copy the directory
        shutil.copytree(src_item, dest_item, dirs_exist_ok=True)
        print(f'Copied directory {src_item} to {dest_item}')
    else:
        # Copy the file
        shutil.copy2(src_item, dest_item)
        print(f'Copied file {src_item} to {dest_item}')

with open(os.path.join('../gen_tests', target_project, f'replay.py'), 'w') as f:
    f.write(script_content)

