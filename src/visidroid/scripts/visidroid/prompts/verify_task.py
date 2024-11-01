from ..config import agent_config
from ..app_state import AppState
from ..model import get_next_assistant_message, zip_messages, get_vision_assistant_message
from ..utils.stringutil import remove_quotes, add_period

import re
import json
import base64
import os
import datetime

MAX_RETRY = 1


def verify_task(memory, prompt_recorder=None):
    user_messages = []
    assistant_messages = []
    system_messages = f"""You are a helpful senior mobile tester who is using an Android mobile application named {agent_config.app_name}.
    
The current task is: "{agent_config.ultimate_goal}". Your goal is base on the history of the task execution, task end condition and the current state of the app in image form to verify the task execution.
""".strip()
    
    user_messages.append(f'''
The current task is: "{agent_config.ultimate_goal}"

Task end condition: {add_period(memory.working_memory.task.end_condition)}

The task execution history (listed in chronological order):
===
{memory.working_memory.stringify_action_with_result()}
===

Based on the task execution history, task end condition and the current state of the app, you need to verify the task execution if the task is done or not. You must take into consideration the task execution history: all the steps must related and the result of action in the final each step should lead to the task end condition. You must pay attention to the all kind of the Apply button ("OK", "apply", "Create", ...), if you want to changes or create something, you must press it to the task to complete.

I am going to provide a template for your output to reason about your next task step by step. Fill out the <...> parts in the template with your own words. Do not include anything else in your answer except the text to fill out the template. Remember to remove the "<>" character and all of my instructions inside that bracket. Preserve the formatting and overall template.

=== Below is the template for your answer ===
Describe the current screen: <1~2 sentences in one line, you should describe all element as you see>
Task done: <yes/no, do not include any other word except "yes" or "no">
'''.strip())
    
    # call vision API
    base64_image = None
    try:
        base64_image = get_base64_image(prompt_recorder)
    except Exception as e:
        print("ERROR: ", e)
        return False, "None"
    
    response = get_vision_assistant_message(system_message=system_messages, user_messages=user_messages, model=agent_config.verifier_model, base64_image=[base64_image])
    assistant_messages.append(response)
    
    print("VISION RESPONSE", response)
    
    def parse_answer(answer):
        task_done = None     
        screen_description = None   
        for l in answer.split('\n'):
            l = l.strip()
            if l.startswith('Describe the current screen:'):
                screen_description = l.removeprefix(f'Describe the current screen:').strip()
            elif l.startswith('Task done:'):
                if 'yes' in l.split('Task done:')[1].strip().lower():
                    task_done = True
                else:
                    task_done = False
        
        return screen_description, task_done
    
    screen_description, task_done = parse_answer(response)
    
    # record the prompt
    if prompt_recorder is not None:
        prompt_recorder.record(zip_messages(system_messages, user_messages, assistant_messages), "verify")
    
    return screen_description, task_done

def get_base64_image(prompt_recorder):
    image_path_temp = os.path.join(agent_config.agent_output_dir, "temp", f"screen_{prompt_recorder.state_tag}.png")
    image_path_state = os.path.join(agent_config.agent_output_dir, "states", f"screen_{prompt_recorder.state_tag}.png")
    try:
        if os.path.exists(image_path_state):
            return encode_image(image_path=image_path_state)
        elif os.path.exists(image_path_temp):
            return encode_image(image_path=image_path_temp)
        elif os.path.exists(decrease_time_by_one_second(image_path_temp)):
            print("Test: " + decrease_time_by_one_second(image_path_temp))
            return encode_image(decrease_time_by_one_second(image_path_temp))
        else:
            raise Exception(f"invalid {image_path_temp} and {image_path_state} and {encode_image(decrease_time_by_one_second(image_path_temp))}")
    except FileNotFoundError:
        raise Exception(f"failed to encode image {image_path_temp} and {image_path_state}")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def decrease_time_by_one_second(string):
    # Split the string into prefix, time part, and extension
    prefix, time_part_with_extension = string.rsplit('_', 1)
    time_part, extension = time_part_with_extension.split('.')
    
    # Parse the time part into a datetime object
    time_obj = datetime.datetime.strptime(time_part, '%H%M%S')

    # Increment the time by 1 second
    time_obj -= datetime.timedelta(seconds=1)

    # Format the updated time part
    updated_time_part = time_obj.strftime('%H%M%S')

    # Return the updated string with the same extension
    return f"{prefix}_{updated_time_part}.{extension}"
