from collections import defaultdict
import chromadb
import time
import os
import re
import json

from .working_memory import WorkingMemory
from .task_memory import TaskMemory
from .spatial_memory import SpatialMemory


class PersistentStorageManager:
    chroma_client = chromadb.Client()
    
    # Use persistent to load data from previous sessions    
    # current_path = os.getcwd()
    # chroma_client = chromadb.PersistentClient(current_path + "/chroma/data")
    active_storages = {
        'primary': None,
        'knowledge': None
    }
    
    @classmethod
    def create_storage(cls, storage_id):
        # try:
        #     cls.chroma_client.delete_collection(name=storage_id)
        # except ValueError:
        #     pass

        # try:
        #     cls.chroma_client.delete_collection(name=f'{storage_id}')
        # except ValueError:
        #     pass

        # cls.active_storages[storage_id] = cls.chroma_client.create_collection(name=storage_id)

        # return cls.active_storages[storage_id]
        
        print(cls.chroma_client.list_collections())
        print(storage_id)
        
        # Create a new collection
        cls.active_storages[storage_id] = cls.chroma_client.get_or_create_collection(name=storage_id)
        return cls.active_storages[storage_id]


class PersistentStorage:
    def __init__(self, name):
        self.name = name
        self.entry_id = 0
        self.db = PersistentStorageManager.create_storage(name)

    def get(self, **kwargs):
        return self.db.get(**kwargs)
    
    def add(self, **kwargs):
        item_count = len(kwargs['documents'])
        ids = list(map(str, range(self.entry_id, self.entry_id + item_count)))
        self.entry_id += item_count

        return self.db.add(documents=kwargs['documents'], metadatas=kwargs['metadatas'], ids=ids)

    def upsert(self, **kwargs):
        self.db.upsert(**kwargs)

    def query(self, **kwargs):
        return self.db.query(**kwargs)

    def add_entry(self, document, metadata, entry_id=None):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if entry_id is None:
            self.entry_id += 1
        else:
            self.entry_id = entry_id

        self.db.upsert(
            documents = [document],
            metadatas = [{
                'timestamp': timestamp,
                **metadata
            }],
            ids = [str(self.entry_id)]
        )

        return str(self.entry_id)

    def _stringify_entry(self, memory_id, metadata, doc, show_timestamp=True, show_type=True):
        if show_type:
            doc = f'[{metadata["type"]}] {doc}\n'
        else:
            doc = f'{doc}\n'

        if show_timestamp:
            return (int(memory_id), f'{metadata["timestamp"]}: {doc}')
        else:
            return (int(memory_id), f'{memory_id}. {doc}')

    def stringify_entries(self, raw_entries, mode='widget_knowledge', show_timestamp=True, show_type=True, max_len=None):
        assert mode in ['task_history', 'widget_knowledge', 'task_knowledge']

        entries = []
        for memory_id, metadata, doc in zip(raw_entries['ids'], raw_entries['metadatas'], raw_entries['documents']):
            if mode == 'task_history':
                if len(doc) == 0:
                    continue
                entries.append(self._stringify_entry(memory_id, metadata, doc, show_timestamp=show_timestamp, show_type=show_type))
            elif mode == 'widget_knowledge':
                knowledge = metadata['observation']
                if len(knowledge) == 0:
                    continue
                action_type = metadata['action']
                entries.append((int(memory_id), f'- result of {action_type}: {knowledge}\n'))
            elif mode == 'task_knowledge':
                knowledge = metadata['reflection']
                if len(knowledge) == 0:
                    continue
                entries.append((int(memory_id), f'- {knowledge}\n'))
            else:
                raise ValueError(f'Unsupported mode for stringifying permanant storage entries: {mode}')

        if len(entries) == 0 and mode == 'task_history':
            return '<no interactions performed yet>'
        
        if len(entries) == 0:
            return ''
            
        entries.sort(key=lambda x: x[0])
        if max_len is not None and isinstance(max_len, int):
            entries = entries[max(-max_len, -len(entries)):]
        
        memory_str = ''
        for memory_id, entry in entries:
            memory_str += entry

        return memory_str.strip()

    def stringify_all_entries(self, mode='widget_knowledge'):
        raw_entries = self.db.get()
        return self.stringify_entries(raw_entries, mode=mode)


class Memory:
    def __init__(self, name):
        self.history = PersistentStorage(f'{name}_primary')
        self.knowledge = PersistentStorage(f'{name}_knowledge')
        self.activity = PersistentStorage(f'{name}_activity_knowledge')
        self.working_memory = WorkingMemory()
        self.task_memory = TaskMemory(self.history, self.knowledge)
        self.widget_knowledge = SpatialMemory(self.knowledge)
        
        # long memory for reserve reflections and optimizations
        self.evaluate_optimized_steps = None
        self.evaluate_rules = None
        
    def set_for_evaluation(self, optimized_steps, rules):
        self.evaluate_optimized_steps = optimized_steps
        self.evaluate_rules = rules
    
    def get_evaluation_steps(self):
        return self.evaluate_optimized_steps
    
    def get_evaluation_rules(self):
        return self.evaluate_rules
        


    def save_snapshot(self, output_dir):
        working_memory_record = self.working_memory.to_dict()
        with open(os.path.join(output_dir, 'scratch.json'), 'w') as f:
            json.dump(working_memory_record, f, indent=2)

        task_history_record = self.history.stringify_all_entries(mode='task_history')
        with open(os.path.join(output_dir, 'long_term_memory.txt'), 'w') as f:
            f.write(task_history_record)

    def collect_knowledge(self):
        widget_knowledge_entries = self.knowledge.get({'where': {'type': 'WIDGET'}})
        task_knowledge_entries = self.knowledge.get({'where': {'type': 'TASK'}})

        task_knowledge = []
        widget_knowledge = defaultdict(lambda: defaultdict(list))

        for memory_id, metadata, state in zip(widget_knowledge_entries['ids'], widget_knowledge_entries['metadatas'], widget_knowledge_entries['documents']):
            if len(metadata['observation']) == 0:
                continue

            action_type = metadata['action']
            widget_knowledge[metadata['page']][metadata['widget']].append((int(memory_id), (action_type, metadata['observation'])))

        for memory_id, metadata, state in zip(task_knowledge_entries['ids'], task_knowledge_entries['metadatas'], task_knowledge_entries['documents']):
            if len(metadata['reflection']) == 0:
                continue

            task_knowledge.append((int(memory_id), (metadata['task'], metadata['reflection'])))

        widget_knowledge_map = copy.deepcopy(self.widget_knowledge.knowledge_map)

        for page, widgets in widget_knowledge.items():
            for widget_signature, w_knowledge in widgets.items():
                observations = widget_knowledge[page][widget_signature]
                widget_knowledge_map[page][widget_signature] = {
                    'summary': w_knowledge,
                    'entries': [obs_entry[1] for obs_entry in observations]
                }

        return task_knowledge, widget_knowledge_map


    def inject_entry(self, description, entry_type):
        self.history.add_entry(description, {'type': entry_type})

    def inject_activity(self, description, entry_id):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        metadata = {'id': entry_id}

        self.activity.upsert(
            documents = [description],
            metadatas = [{
                'timestamp': timestamp,
                **metadata
            }],
            ids = [str(entry_id)]
        )

        return str(entry_id)
