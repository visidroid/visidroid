from ..config import agent_config
from ..app_state import AppState
from ..model import get_next_assistant_message, zip_messages
from ..functions.possible_actions import *
from ..utils import *

QUERY_COUNT = 3

# Do we need long-term view?
# Inference on the remaining steps needed to complete the task: <1~2 sentences according to the memory, current app state, and the task end condition>


def prompt_action(memory, prompt_recorder=None):
    possible_action_functions, function_map = initialize_possible_actions()

    system_message = f'''
You are a helpful assistant to guide a user named {agent_config.persona_name} to select an appropriate GUI action to accomplish a task on an Android mobile application named {agent_config.app_name}.

{agent_config.persona_name} can perform the following types of actions:
- Scroll on a scrollable widget
- Touch on a clickable widget
- Long touch on a long-clickable widget
- Fill in an editable widget
- Navigate back by pressing the back button
or end the task if the task is already completed.
'''.strip()

    user_messages, assistant_messages = memory.working_memory.make_virtual_conversation()

    # extract the observation from the last user message (this time, the user query is "real" so we need to be more in detail)
    last_observation = user_messages[-1].strip()

    user_messages.pop()
    user_messages.append(f'''
{last_observation}

This time, I'll give you the full content of the current page as follows (I organized the page content as a hierarchical structure):
```json
{AppState.current_gui_state.describe_screen_w_memory(memory, include_widget_knowledge=False)}
```
Note that `num_prev_actions` property means the number of times the widget has been interacted with so far.

Recall that my current task is: {memory.working_memory.task.summary}
Select the next suitable action to perform, or end the task if the task is already completed.

This time, I am going to provide a template for your output to let you think about my next action step by step. Fill out the <...> parts in the template with your own words. Do not include anything else in your answer except the text to fill out the template. Preserve the formatting and overall template.

=== Below is the template for your answer ===
1. Summary of my previous interactions for the task: <1~2 sentences according to the task execution history and current app state. Be careful not to include any actions that haven't been performed yet>
2. Description of the current app state: <1~2 sentences, briefly describe in one line according to the hierarchical structure I provided above>
3. Inference on the remaining steps needed to complete the task: <1~2 sentences according to the task execution history and current app state. Do not immediately judge the next action here>
4. Reasoning for the next action: <1 sentence reasoning the most logical action to take next on the current state (or justification for ending the task). Refer to the guideline above>
'''.strip())

    assistant_messages.append(get_next_assistant_message(system_message, user_messages, assistant_messages, model=agent_config.actor_model, functions=list(possible_action_functions.values()), function_call_option="none")) # just reasoning this time

    return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, prompt_recorder=prompt_recorder)


def prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=None, prompt_recorder=None, query_count=QUERY_COUNT):
    if query_count == 0:
        if prompt_recorder is not None:
            prompt_recorder.record(zip_messages(system_message, user_messages, assistant_messages), 'action')
        return None

    if error_message is None:
        action_function_query = f'''
Based on your reasoning, select the next action or end the task by calling one of the given function that corresponds to a specific action.'''.strip()

        user_messages.append(action_function_query)

    else:
        user_messages.append(error_message)

    assistant_messages.append(get_next_assistant_message(system_message, user_messages, assistant_messages, model=agent_config.actor_model, functions=list(possible_action_functions.values())))
    response = assistant_messages[-1]

    if not isinstance(response, dict): # retry if model doesn't do function call
        error_message = f'You need to call a function to select the next action or end the task for {agent_config.persona_name}.'
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    function_to_call = function_map[response['name']]
    function_params = []
    for param_name in possible_action_functions[response['name']]['parameters']['properties']:
        function_params.append(param_name)

    try:
        function_args = json.loads(response['arguments'])
    except json.decoder.JSONDecodeError:
        error_message = f'You did not provide the required parameters for the function call. Please provide the following parameters: {function_params}'
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    processed_function_args = {}
    error_message = None
    for param_name in function_params:
        arg_value = function_args.get(param_name)
        if arg_value is None:
            error_message = f'You did not provide the required parameter "{param_name}".'
            break
        if param_name == 'target_widget_id':
            try:
                arg_value = int(arg_value)
            except ValueError:
                error_message = f'The value of the parameter "{param_name}" should be an integer.'
                break
        processed_function_args[param_name] = arg_value

    if error_message is not None: # retry if model doesn't make correct arguments
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    action, error_message = function_to_call(**processed_function_args)

    if error_message is not None: # retry if target widget ID is not valid
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    if action is not None and action.event_type == 'set_text':
        text_input = prompt_text_input(memory, system_message, user_messages, assistant_messages, action.target_widget, prompt_recorder=prompt_recorder)
        action.update_input_text(text_input)
        return action
    
    if prompt_recorder is not None:
        prompt_recorder.record(zip_messages(system_message, user_messages, assistant_messages), 'action')

    return action


def prompt_text_input(memory, system_message, user_messages, assistant_messages, target_widget, prompt_recorder=None, caller='actor'):
    follow_up_question = f'''
Good. From now on, act as you are {agent_config.persona_name} and provide the text to be inputted in the selected textfield (Widget ID: {target_widget.view_id}). 

The properties and children (if any) of the selected textfield are as follows:
{target_widget.dump()}

You need to generate concrete text content to be filled in the textfield by inferring the content based on my profile.

I am going to provide a template for your output step by step.
=== Below is the template for your answer ===
Role of the textfield: <1~2 sentences>
Reasoning for generating {agent_config.persona_name}'s text: <1~2 sentences>
Text: <generated text content>

=== Below is the example of a valid answer format ===
Role of the textfield: The textfield is for inputting the user's full name.
Reasoning for generating proper text: {agent_config.persona_name} should input their own name in the textfield.
Text: {agent_config.persona_name}
'''.strip()

    user_messages.append(follow_up_question)

    received_text = None
    for _ in range(QUERY_COUNT):
        assistant_messages.append(get_next_assistant_message(system_message, user_messages, assistant_messages, model=agent_config.actor_model, function_call_option="none"))
        response = assistant_messages[-1]
        for l in response.split('\n'):
            l = l.strip()
            if l.startswith('Text:'):
                received_text = l.strip().removeprefix('Text:').strip().strip('"').strip()
                break
        if received_text is not None:
            break
        
        error_message = f'You did not provide the text in the required template. Please provide the text in the following format: "Text:<your text>". For example, if you want to input "Hello World" into the textfield, you should answer with "Text:Hello World".'
        user_messages.append(error_message)

    if received_text is None:
        received_text = 'HelloWorld'
    
    if prompt_recorder is not None:
        tag = 'action_data_text'
        if caller == 'planner':
            tag = 'plan'
        prompt_recorder.record(zip_messages(system_message, user_messages, assistant_messages), tag)
    
    return received_text
