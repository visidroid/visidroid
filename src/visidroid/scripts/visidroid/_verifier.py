import os
import logging

from .config import agent_config
from .model import APIUsageManager
from .types.action import *
from .utils.logger import Logger
from .prompts.verify_task import verify_task


logger = Logger(__name__)


class Verifier:
    def __init__(self, memory, prompt_recorder=None):
        self.memory = memory
        self.prompt_recorder = prompt_recorder

    def verify_action_result(self):
        task = self.memory.working_memory.task

        screen_description, task_done = verify_task(self.memory, self.prompt_recorder)
        
        # task.add_result(task_result, task_result_summary)
        # self.memory.task_memory.record_task_result(task, reflections, self.memory.working_memory.steps)
        
        self.memory.working_memory.set_task_done(task_done)

        return screen_description
