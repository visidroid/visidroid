import os
import json
import time


from .app_state import AppState
from .memories.memory import Memory
from .utils.prompt_recorder import PromptRecorder
from .utils.logger import Logger
from .model import APIUsageManager

from .config import agent_config

from ._observer import Observer
from ._planner import Planner
from ._actor import Actor
from ._reflector import Reflector
from ._verifier import Verifier


from .prompts.state_comparation import state_comparation

os.environ['TOKENIZERS_PARALLELISM'] = 'false'

MODE_PLAN = 'plan'
MODE_ACT = 'act'
MODE_REFLECT = 'reflect'
MODE_OBSERVE = 'observe'
MODE_VERIFY = 'verify'

MAX_ACTIONS = 13

# Number of times to run the task
# TODO: Move to arg
MAX_RUN = 3

logger = Logger(__name__)
    
class Agent:
    def __init__(self, output_dir, app=None, device=None):
        if app is None:
            raise NotImplementedError # TODO: load agent snapshot from output_dir
        
        else:
            agent_config.set_app(app)
            agent_config.set_output_dir(output_dir)
            agent_config.save()
            
            # log agent_config app name
            logger.info(f'Agent Config App Name: {agent_config.app_name}')

            # exp_id is app name for memory to create persistent data every run time
            safe_exp_id = agent_config.app_name.replace(' ', '_').replace('.', '_')
            self.exp_id = agent_config.app_name
            self.prompt_recorder = PromptRecorder()
            self.memory = Memory(name=safe_exp_id)

        AppState.initialize(agent_config.app_name, agent_config.app_activities)
        logger.info(f'Initialized an Agent with ID: {agent_config.app_name}')

    def save_memory_snapshot(self):
        memory_snapshot_dir = os.path.join(agent_config.agent_output_dir, 'memory_snapshots', f'step_{self.step_count}')
        os.makedirs(memory_snapshot_dir, exist_ok=True)
        self.memory.save_snapshot(memory_snapshot_dir)

    def step(self, droidbot_state=None):
        raise NotImplementedError

    def set_current_gui_state(self, droidbot_state):
        AppState.set_current_gui_state(droidbot_state)
        self.prompt_recorder.set_state_tag(AppState.current_gui_state.tag)

    @property
    def exp_data(self):
        return {
            'app_activities': AppState.activities,
            'visited_activities': AppState.visited_activities,
            'task_results': self.memory.task_memory.task_results,
            'API_usage': APIUsageManager.usage,
            'API_response_time': APIUsageManager.response_time
        }


class VisiDroidFull(Agent):
    """
    Specific Task-based Agent
    """
    def __init__(self, output_dir, app=None, persona=None, debug_mode=False, device=None):
        super().__init__(output_dir, app=app, device=device)

        if app is None:
            raise NotImplementedError # TODO: load agent snapshot from output_dir
        else:
            self.initialize(app, persona, debug_mode=debug_mode, device=device)

        logger.info(f'Target App: {agent_config.app_name} ({agent_config.package_name})')
        logger.info(f'Ultimate Goal: {agent_config.ultimate_goal}')
        self.ultimate_goal = agent_config.ultimate_goal

    def initialize(self, app, persona, debug_mode=False, device=None):
        for initial_knowledge in persona['initial_knowledge']:
            self.inject_knowledge_entry(initial_knowledge, 'INITIAL_KNOWLEDGE')
        
        if debug_mode:
            agent_config.set_debug_mode()
            
        agent_config.set_persona(persona)
        agent_config.save()

        self.observer = Observer(self.memory, self.prompt_recorder)
        self.planner = Planner(self.memory, self.prompt_recorder)
        self.actor = Actor(self.memory, self.prompt_recorder)
        self.reflector = Reflector(self.memory, self.prompt_recorder)
        self.verifier = Verifier(self.memory, self.prompt_recorder)
        self.mode = MODE_PLAN
        
        # === Support app back to main activity each runtime
        self.device = device
        self.app = app
        # ===
        
        self.reflections = ""
        self.optimizations = ""
        self.step_count = 0
        self.run_count = 0
        
        # Support get finalize data only 1 time
        self.is_finalize = False

    @property
    def task(self):
        return self.memory.working_memory.task

    @property
    def persona_name(self):
        return agent_config.persona_name
    
    def compare_state(self): 
        return state_comparation(memory=self.memory)

    def step(self, droidbot_state=None):
        self.step_count += 1
        logger.info(f"Step {self.step_count}, Mode: {self.mode}")
        logger.info(
            f"Current Activity Coverage: {len(AppState.visited_activities)} / {len(agent_config.app_activities)}"
        )

        if droidbot_state is not None:
            self.set_current_gui_state(droidbot_state)

        with open(
            os.path.join(agent_config.agent_output_dir, "exp_data.json"), "w"
        ) as f:
            json.dump(self.exp_data, f, indent=2)

        if self.mode == MODE_PLAN:
            """
            * Plan
            """

            self.actor.reset()
            first_action = self.planner.plan_task()

            # If this phase is evaluate phase, we get rules and history from training phase
            if agent_config.train is None:
                if not self.is_finalize:
                    self.reflector.finalize()

                    self.reflections = self.memory.get_evaluation_rules()
                    self.optimizations = self.memory.get_evaluation_steps()
                    self.is_finalize = True

            if first_action is not None:
                self.mode = MODE_OBSERVE
                self.actor.action_count += 1
                self.actor.critique_countdown -= 1
                logger.info(f'* New task: {self.task}')
                logger.info(f'* First action: {first_action}')

                return first_action

            return None
        
        elif self.mode == MODE_REFLECT:
            """
            * Reflect
            """
            self.run_count += 1

            task_result_summary, task_result, reflections, optimizations = self.reflector.reflect()
            # Training phase
            if agent_config.train is not None:
                reflections_path = os.path.join(agent_config.agent_output_dir, '..', f'{agent_config.app_name}_train.json')

                self.reflections = reflections
                self.optimizations = optimizations
                
            # Evaluate phase
            else:
                reflections_path = os.path.join(agent_config.agent_output_dir, '..', f'{agent_config.app_name}_evaluate.json')

                # If succeed, keep the rules and history from training phase
                if task_result == 'SUCCESS':
                    self.reflections = self.memory.get_evaluation_rules()
                    self.optimizations = self.memory.get_evaluation_steps()
                # else get from reflector
                else: 
                    self.reflections = reflections
                    self.optimizations = optimizations
            logger.info(f'* Task Reflection: {task_result_summary}')
            
            self.mode = MODE_PLAN
            if os.path.exists(reflections_path):
                with open(os.path.join(reflections_path), 'r') as f:
                    existing_data = json.load(f)
                    reflections_data = {
                        'summary': task_result_summary,
                        'task_result': task_result,
                        'optimization': optimizations,
                        'reflections': reflections,
                        'history_action': self.memory.working_memory.stringify_action()
                    }
                if self.memory.working_memory.task.summary in existing_data:
                    existing_data[self.memory.working_memory.task.summary].append(reflections_data)
                    self.reflect_data = existing_data
                else:
                    existing_data[self.memory.working_memory.task.summary] = [{
                        'summary': task_result_summary,
                        'task_result': task_result,
                        'optimization': optimizations,
                        'reflections': reflections,
                        'history_action': self.memory.working_memory.stringify_action()
                    }]
                    self.reflect_data = existing_data
            else:
                self.reflect_data = {
                    self.memory.working_memory.task.summary: [{
                        'summary': task_result_summary,
                        'task_result': task_result,
                        'optimization': optimizations,
                        'reflections': reflections,
                        'history_action': self.memory.working_memory.stringify_action()
                    }]
                }
            # print(self.reflect_data)
            with open(os.path.join(reflections_path), 'w') as f:
                json.dump(self.reflect_data, f, indent=2)
                        
            # Stop if run time is reached
            if self.run_count >= MAX_RUN or task_result and (agent_config.train is not None or agent_config.evaluate is not None):
                with open(os.path.join(agent_config.agent_output_dir, 'exp_data.json'), 'w') as f:
                    json.dump(self.exp_data, f, indent=2)
                result = True if task_result == 'SUCCESS' else False

                # reset app back to main activity
                self.device.stop_app(self.app)
                time.sleep(1)
                self.device.start_app(self.app)
                time.sleep(1)
                
                return result
            
            # reset app back to main activity
            self.device.stop_app(self.app)
            time.sleep(1)
            self.device.start_app(self.app)
            time.sleep(1)
            
            return "Reflection"

        elif self.mode == MODE_ACT:
            """
            * Action
            """
            logger.info(f'[Current Task] {self.task}')

            if self.actor.action_count >= MAX_ACTIONS:
                # If task does not end after MAX_ACTIONS actions, reflect
                self.mode = MODE_REFLECT
                self.inject_action_entry('The task gets too long, so I am going to put off the task and start a new task that could be easily achievable instead.', 'TASK_ABORTED')
                logger.info(f'Task not completed with max actions, aborting...')
                return None

            next_action = self.actor.act(self.reflections, self.optimizations)

            if next_action is None:
                self.mode = MODE_REFLECT
                return None
            else:
                logger.info(f'* Next action: {next_action}')
                self.mode = MODE_OBSERVE
                return next_action

        elif self.mode == MODE_OBSERVE:
            """
            * Observe
            """
            
            action_result = self.observer.observe_action_result()
            if action_result is not None:
                logger.info(f'* Observation: """\n{action_result}\n"""')
            else:
                logger.info(f'* Observation: No detectable change.')

            # TODO: Check if we really need to verify when debug, if not, disable it
            # self.mode = MODE_ACT
            self.mode = MODE_VERIFY
            return None
        elif self.mode == MODE_VERIFY:
            """
            * Verify
            """

            self.screen_description = self.verifier.verify_action_result()
            print(f"Screen description: {self.screen_description}")
            self.mode = MODE_ACT

            return None
            # if is_done == False:
            #     self.mode = MODE_ACT
            #     return action_result
            # else:
            #     self.mode = MODE_REFLECT
            #     return action_result
            

    def inject_knowledge_entry(self, description, entry_type):
        self.memory.inject_entry(description, entry_type)

    def inject_action_entry(self, description, entry_type):
        self.memory.working_memory.add_step(description, AppState.current_activity, entry_type)

    def inject_activity_knowledge(self, description, entry_type):
        self.memory.inject_activity(description, entry_type)
