from ..config import agent_config
from ..app_state import AppState
from ..model import get_next_assistant_message, zip_messages
from ..functions.possible_actions import *
from ..utils.stringutil import *
from .act import prompt_text_input, initialize_possible_actions

QUERY_COUNT = 3

"""
1. Persona-based exploration w/ custom testing objective
"""
def prompt_new_task(memory, prompt_recorder=None):
    # TODO: refer to spatial memory - what is the current page? what are the widgets in the current page?
    # TODO: refer to temporal memory - what are the memorable tasks so far?
    unvisited_pages = list(set(AppState.activities) - set(AppState.visited_activities.keys()))

    system_message = f'''
You are a helpful task planner for using an Android mobile application named {agent_config.app_name}. 

{agent_config.persona_name}'s task is: {agent_config.ultimate_goal}. You need to help {agent_config.persona_name} to successfully complete the task.
- {agent_config.app_name} app has following pages: {remove_quotes(str(AppState.activities))} (Note that the pages are listed in random order)
- Currently, {agent_config.persona_name} has visited the following pages with the following number of times: {remove_quotes(json.dumps(AppState.visited_activities))}
- Currently, {agent_config.persona_name} is on the {AppState.current_gui_state.activity} page.
- Pages never visited yet: {remove_quotes(str(unvisited_pages))} 
'''.strip()

    assistant_messages = []

    # set of user messages for planner
    user_messages = [f'''
{agent_config.persona_name}'s task is: {agent_config.ultimate_goal}.

{agent_config.persona_name}'s prior knowledge and history of previous tasks so far (listed in chronological order):
===
{memory.task_memory.retrieve_task_history()}
===

{agent_config.persona_name}'s learnt knowledge from previous tasks (which may be relevant to the current context):
===
{memory.task_memory.retrieve_task_reflections(AppState.current_gui_state)}
===

Current page (organized in a hierarchical structure):
```json
{AppState.current_gui_state.describe_screen_w_memory(memory, prompt_recorder=prompt_recorder)}
```
Note that `num_prev_actions` means the number of times the widget has been interacted with during the previous tasks. If `num_prev_actions` property is not included in the widget dictionary, {agent_config.persona_name} has never performed any action on the widget yet.

{agent_config.persona_name} can perform the following types of actions:
- Scroll on a scrollable widget
- Touch on a clickable widget
- Long touch on a long-clickable widget
- Fill in an editable widget
- Navigate back by pressing the back button

I am going to provide a template for your output to reason about your next task step by step. Fill out only the <...> parts in the template with your own words. Do not include anything else in your answer except the text to fill out the template. Remember to remove the "<>" bracket. Preserve the formatting and overall template.

=== Below is the template for your answer ===
End condition of {agent_config.persona_name}'s next task: <1 sentence, start with "The task is known to be completed when">
Reasoning of the first action of the {agent_config.persona_name}'s next task: <reasoning and description of the first action initiating the task>
Rough plan for the task in {agent_config.persona_name}'s perspective: <1 sentence, start with "I plan to"; pretend that you are {agent_config.persona_name}>
'''.strip()]

    # Let the planner select the first action
    possible_action_functions, function_map = initialize_possible_actions()

    assistant_messages.append(get_next_assistant_message(system_message, user_messages, assistant_messages, model=agent_config.planner_model, functions=list(possible_action_functions.values()), function_call_option="none"))

    def parse_answer(answer):
        task = None
        task_end_condition = None
        plan = []
        for l in answer.split('\n'):
            l = l.strip()
            if l.startswith(f'End condition of {agent_config.persona_name}\'s next task:'):
                task_end_condition = l.removeprefix(f'End condition of {agent_config.persona_name}\'s next task:').strip()
            elif l.startswith(f'Rough plan for the task in {agent_config.persona_name}\'s perspective:'):
                plan = l.removeprefix(f'Rough plan for the task in {agent_config.persona_name}\'s perspective:').strip()


        return agent_config.ultimate_goal, task_end_condition, plan

    task, end_condition, plan = parse_answer(assistant_messages[-1])

    valid_task = False
    for i in range(QUERY_COUNT):
        if task is not None and end_condition is not None and len(task) > 0 and len(end_condition) > 0:
            valid_task = True
            break
        retry_message = f'''You did not give a correct answer following the given template after the line "=== Below is the template for your answer ===".'''
        user_messages.append(retry_message)

        assistant_messages.append(get_next_assistant_message(system_message, user_messages, assistant_messages, model=agent_config.planner_model))
        task, end_condition, plan = parse_answer(assistant_messages[-1])

    if not valid_task:
        if prompt_recorder is not None:
            prompt_recorder.record(zip_messages(system_message, user_messages, assistant_messages), 'plan')
        return None, None, None, None

    task = task[0].upper() + task[1:]

    first_action = prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, prompt_recorder=prompt_recorder)

    if first_action is None:
        # Maybe the plan is not feasible, let's plan again
        return None, None, None, None

    return task, end_condition, plan, first_action


def prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=None, prompt_recorder=None, query_count=QUERY_COUNT):
    if query_count == 0:
        if prompt_recorder is not None:
            prompt_recorder.record(zip_messages(system_message, user_messages, assistant_messages), 'plan')
        return None

    if error_message is None:
        action_function_query = f'''
Good. Now, based on your previous answer, execute the first action (by calling a function) to start the task. Pay attention to the possible action types specified in the target widget.'''.strip()

        user_messages.append(action_function_query)

    else:
        user_messages.append(error_message)

    assistant_messages.append(get_next_assistant_message(system_message, user_messages, assistant_messages, model=agent_config.actor_model, functions=list(possible_action_functions.values())))
    response = assistant_messages[-1]

    if isinstance(response, str): # retry if model doesn't do function call
        error_message = f'Call one of the given function instead of text answers.'
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    if response['function']['name'] not in possible_action_functions: # retry if model doesn't do a right function call
        error_message = {
            'tool_call_id': response['id'],
            'name': respone['function']['name'],
            'return_value': json.dumps({
                'error_message': f'You need to call a function among the given functions to select the next action or end the task for {agent_config.persona_name}. {response["function"]["name"]} is not a valid function name.'
            })
        }
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    function_name = response['function']['name']
    function_to_call = function_map[function_name]
    function_params = []
    for param_name in possible_action_functions[function_name]['function']['parameters']['properties']:
        function_params.append(param_name)

    try:
        function_args = json.loads(response['function']['arguments'])
    except json.decoder.JSONDecodeError:
        error_message = {
            'tool_call_id': response['id'],
            'name': respone['function']['name'],
            'return_value': json.dumps({
                'error_message': f'You did not provide the suitable parameters for the function call. Please provide the following parameters: {function_params}'
            })
        }
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    processed_function_args = {}
    error_message = None
    for param_name in function_params:
        arg_value = function_args.get(param_name)
        if arg_value is None:
            error_message = {
                'tool_call_id': response['id'],
                'name': respone['function']['name'],
                'return_value': json.dumps({
                    'error_message': f'You did not provide the required parameter "{param_name}".'
                })
            }
            break
        if param_name == 'target_widget_ID':
            try:
                arg_value = int(arg_value)
            except ValueError:
                error_message = {
                    'tool_call_id': response['id'],
                    'name': respone['function']['name'],
                    'return_value': json.dumps({
                        'error_message': f'The value of the parameter "{param_name}" should be an integer.'
                    })
                }
                break
        processed_function_args[param_name] = arg_value

    if error_message is not None: # retry if model doesn't make correct arguments
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)

    action, error_message = function_to_call(**processed_function_args)

    if error_message is not None: # retry if target widget ID is not valid
        error_message = {
            'tool_call_id': response['id'],
            'name': response['function']['name'],
            'return_value': json.dumps({
                'error_message': error_message
            })
        }
        return prompt_action_function(memory, system_message, user_messages, assistant_messages, possible_action_functions, function_map, error_message=error_message, prompt_recorder=prompt_recorder, query_count=query_count-1)
    
    if action is not None and action.event_type == 'set_text':
        text_input = prompt_text_input(memory, system_message, user_messages, assistant_messages, action.target_widget, prompt_recorder=prompt_recorder, caller='planner')
        action.update_input_text(text_input)
        return action

    if prompt_recorder is not None:
        prompt_recorder.record(zip_messages(system_message, user_messages, assistant_messages), 'plan')

    return action