from ..config import agent_config
from ..app_state import AppState
from ..model import get_next_assistant_message, zip_messages
from ..utils.stringutil import remove_quotes

import re
import json

MAX_RETRY = 1

def reflect_task(memory, prompt_recorder=None):
    task = memory.working_memory.task.summary
    system_message = f'''You are a helpful task reflector for a person named "{agent_config.persona_name}" who is using an Android mobile application named {agent_config.app_name}.

{agent_config.persona_name} is performing the task: "{agent_config.ultimate_goal}".
    - The app has following pages: {remove_quotes(str(agent_config.app_activities))}
    - Currently, {agent_config.persona_name} is on the {AppState.current_gui_state.activity} page.

Currently, {agent_config.persona_name} has performed actions to accomplish the following task: {task}

{agent_config.persona_name} wants to summarize the result of the task and 
    '''.strip()

    assistant_messages = []
    user_messages = []
    user_messages.append(f'''
Summarize the result of the task, and reflect on the task execution.

Full task execution history:
===
{memory.working_memory.stringify()}
===

Widgets in the current page (page name: {AppState.current_gui_state.activity}):
===
{AppState.current_gui_state.describe_widgets_NL(length_limit=8000)}
===

Guideline for the task reflection based on the task result:
- If the task is successful, provide a learned knowledge about the app functionality. (e.g., "The app supports the task X by doing Y.")
- If the task is successful but with excessive steps, point out the step that should be the final step to accomplish the task.
- If the task is failed, reflect why {agent_config.persona_name} failed to accomplish the task and provide lessons learned from the failure. (e.g., "{agent_config.persona_name} once tried to do X but couldn't do Y. It seems that {agent_config.persona_name} might have to do Z before doing Y.")
- The rules will be provided to {agent_config.persona_name} to help doing the same task again with more accuracy and avoid previous mistakes. Keep the rules to be self-contained (briefly include what the target task was) and concise.

I am going to provide a template for your output to reason about your answer step by step. Fill out the <...> parts in the template with your own words. Do not include anything else in your answer except the text to fill out the template. Preserve the formatting and overall template.

=== Below is the template for your answer ===
Summary of the task result: <1~2 sentences, summary of the result of the task>
Task done successfully?: <yes/no, do not include anything else in your answer>
Optimized steps to accomplish the task:
1.  <Describe all the actions above with natural language to guide the chatGPT when doing this task again. Remove any excessive actions, or point out the actions that is wrong.>
2.  <...provide up to 10 items>
Rules on the task:
- <1 sentence for each item, this strict rule will be used to guide chatGPT to avoid previous mistake, or do the task with more accuracy>
<...provide up to 2 items>'''.strip())

    assistant_messages.append(get_next_assistant_message(system_message, user_messages, assistant_messages, model=agent_config.reflector_model))

    gpt_response = assistant_messages[-1].strip()
    task_result = assistant_messages[-1].strip()

    task_result_summary = None
    reflections = []
    optimizations = []
    task_success = None

    for l in task_result.split('\n'):
        l = l.strip()
        if l.startswith('Summary of the task result:'):
            task_result_summary = l.split('Summary of the task result:')[1].strip()
        elif l.startswith('-'): # app fact
            reflection = '-'.join(l.split('-')[1:]).strip()
            reflections.append(reflection)
        elif l.startswith('Task done successfully?:'):
            task_success = l.split('Task done successfully?:')[1].strip().lower()
            if 'yes' in task_success:
                task_success = True
            elif 'no' in task_success:
                task_success = False
        elif l.startswith(tuple(str(i) for i in range(10))):
            optimizations.append(l)
    if prompt_recorder is not None: 
        prompt_recorder.record(zip_messages(system_message, user_messages, assistant_messages), 'reflect')

    task_result = 'SUCCESS' if task_success else 'FAILURE'

    return task_result_summary, task_result, reflections, optimizations