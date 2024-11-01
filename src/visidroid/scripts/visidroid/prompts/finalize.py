from ..config import agent_config

from ..model import get_next_assistant_message, zip_messages
from ..functions.possible_actions import *
from ..utils import *

import os

MAXIMUM_TRAIN_COUNT = 3
#Tách ra hay gom lại tuỳ, tách ra thì t nghĩ tốt hơn để nó tập trung vô đc 1 thứ th nhưng bị prommpt nhiều
def finalize_task(memory, prompt_recorder=None):
    user_message = []
    assistant_messages = []
    system_message = f""" You are a expert mobile tester. You have been doing the task: "{agent_config.ultimate_goal}" on the Android mobile application named {agent_config.app_name} for a while now.
    
    Your goal is based on all the previous training phases, you need to finalize the correct action history and the strict rules for software engineer to follow in the future. They must be albe to complete the task successfully and efficiently if they follow your guidance.
    """.strip()
    
    user_message.append(f'''
    The current task is: "{agent_config.ultimate_goal}" on the Android mobile application named {agent_config.app_name}                        
                        
    I'm going to give you a summary of all the training phases you have done so far. These data included: Result, Rules, and History Action. You need to finalize the History Action and Reflections Rules for the future software engineer to follow. If they follow your guidance, they will be able to complete the task successfully and efficiently.
                        '''.strip())
    
    train_data = get_training_data(memory=memory)
    # train_data[0]["task_result"] => task_result
    # train_data[0]["summary"] => summary
    # train_data[0]["reflections"] => reflections
    # train_data[0]["optimizations"] => optimizations
    # train_data[0]["history_action"] => history_action
    counter = 1
    for data in train_data:
        user_message[0] += f"""
        *** TRAINING PHASE {counter}:
        Task Result: {data["task_result"]}
        Rules:"""

        # Iterating over reflections and adding them as bullet points
        for reflection in data["reflections"]:
            user_message[0] += f"\n- {reflection}"

        user_message[0] += f"""
        Optimization:"""
        for optimization in data["optimization"]:
            user_message[0] += f"\n{optimization}"

        user_message[0] += f"""
        History Action: {data["history_action"]}
        """
        counter += 1

        # Cái trên sẽ là
        # TRAINING PHASE 1:
        # Task Result : Success/Failed
        # Summary: Summary
        # Reflections: 
        # - reflect 1
        # - reflect 2
        # - reflect 3
        # Optimization:
        # 1. 
        # 2. 
        # 3. ....
        # upto 10
        # History Action:
        # Đang ở dạng string => có chứa \n này nọ giữ nguyên bỏ prommpt là đc nhưng bị cái ACTION ko liên tục như ACTION 1 ACTION 3 ACTION 7 ....
    template = """ \n
I am going to provide a template for your output to reason about your next task step by step. Fill out the <...> parts in the template with your own words. Do not include anything else in your answer except the text to fill out the template. Remember to remove the "<>" character and all of my instructions inside that bracket. Preserve the formatting and overall template.

=== Below is the template for your answer ===
History:
1. <Give me only the neccessary steps to complete the task. One step is 1 action>
2. <... provide up to 10 steps>
Rules on the task:
- <1 sentence for each item, this strict rule will be used to guide chatGPT to avoid previous mistake, or do the task with more accuracy>
<...provide up to 3 items>
    """.strip()
    
    user_message[0] += template
    
    assistant_messages.append(get_next_assistant_message(system_message, user_message, assistant_messages, model=agent_config.reflector_model))
    
    # get gpt response
    gpt_response = assistant_messages[-1]
    
    # construct variable
    optimizations = []
    reflections = []
    
    for l in gpt_response.split('\n'):
        l = l.strip()
        if l.startswith('-'):
            reflection = '-'.join(l.split('-')[1:]).strip()
            reflections.append(reflection)
        elif l.startswith(tuple(str(i) for i in range(10))):
            optimizations.append(l)
    
    print("Optimizations: ", optimizations)
    print("Reflections: ", reflections)
    
    # Record
    if prompt_recorder is not None:
        prompt_recorder.record(zip_messages(system_message, user_message, assistant_messages), 'finalize')
    
    return optimizations, reflections

def get_training_data(memory):
    reflections_path = os.path.join(agent_config.agent_output_dir, '..', f'{agent_config.app_name}_train.json')
    if os.path.exists(reflections_path):
        with open(os.path.join(reflections_path), 'r') as f:
            data = json.load(f)
            train_data = data[memory.working_memory.task.summary]

            return train_data

    else:
        ##Return sth that will continue to run without training data
        raise Exception("Task have not been trained yet")


