from ..config import agent_config

from ..model import get_next_assistant_message, zip_messages, get_vision_assistant_message
from ..functions.possible_actions import *
from ..utils import *
from ..utils.stringutil import add_period

import os
import base64
MAXIMUM_TRAIN_COUNT = 3
def state_comparation(memory, screens = [],prompt_recorder=None):
    user_message = []
    assistant_messages = []
    system_message = f""" You are a helpful senior mobile tester who is using an Android mobile application named Contacts.\nThe current task is: "{agent_config.ultimate_goal}" on the Android mobile application named {agent_config.app_name} for a while now.
    
    Your goal is base on the history of the task execution, task end condition and the current state of the app in image to verify the task execution.
    """.strip()
    
    user_message.append(f'''
    The current task is: "{agent_config.ultimate_goal}" on the Android mobile application named {agent_config.app_name}                        
                        
    Task end condition: "{add_period(memory.working_memory.task.end_condition)}".
    I have {len(screens)} screens activity, you have to check that which screen is suitable for the end condition of this tasks. You have to choose that base on the guide below:
    - The screen have to display full information about the tasks end condition.
    - The screen have to display the result of the tasks.
    - The screen is not relate should be excluded
                        '''.strip())    
    template = """ \n
    ======== TEMPLATE ==========
    Images that could be the final result: <1~2 id ONLY in one line seperate with comma whether it make sense for the final result of the task>
    """.strip()
    
    user_message[0] += template

    screen_descriptions, base64_images = get_base64_image_and_description()
    if screen_descriptions is None:
        return None, None
    for i, content in enumerate(screen_descriptions):
        user_message.append(f"Image ID: {i}\nImage Content: {content}")

    assistant_messages.append(get_vision_assistant_message(system_message, user_message, assistant_messages, model=agent_config.verifier_model, base64_image=base64_images))
    
    # get gpt response
    gpt_response = assistant_messages[-1]
    
    # construct variable
    images_id_assertion = ""
    images_id_final_screen = ""
    for l in gpt_response.split('\n'):
        l = l.strip()
        if l.startswith('Images that could be the final result:'):
            images_id_final_screen = l.removeprefix('Images that could be the final result:')
    
    print("Assertion: ", images_id_assertion)
    print("Final Screen: ", images_id_final_screen)
    
    # Record
    if prompt_recorder is not None:
        prompt_recorder.record(zip_messages(system_message, user_message, assistant_messages), 'finalize')
    
    return images_id_assertion, images_id_final_screen


def get_base64_image_and_description():
    evaluate_folder = os.path.join(agent_config.agent_output_dir, "evaluation_phase")
    image_paths = []
    screen_descriptions_path = []
    screen_descriptions = ["None"]

    base64_images = []
    for item in os.listdir(evaluate_folder):
        image_paths.append(os.path.join(evaluate_folder, item, "evaluation_phase.png"))
        screen_descriptions_path.append(os.path.join(evaluate_folder, item, "screen_description.txt"))
    valid_image_paths = []
    valid_screen_descriptions = []

    for i, item in enumerate(image_paths):
        if os.path.exists(item):
            valid_image_paths.append(image_paths[i])
            valid_screen_descriptions.append(screen_descriptions_path[i])

    if len(valid_image_paths) == 0:
        return None, None

    # Update the original lists
    image_paths = valid_image_paths
    screen_descriptions_path = valid_screen_descriptions

    for path in image_paths:    
        base64_images.append(encode_image(image_path=path))

    for path in screen_descriptions_path:
        with open(path, 'r') as f:
            content = f.read()
            screen_descriptions.append(content) 

    return screen_descriptions, base64_images

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
