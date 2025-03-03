import time
import os
import shutil
import json
import argparse
import subprocess
import shlex

# from timeout_decorator import timeout

from droidbot.device import Device
from droidbot.app import App
from droidbot.input_event import IntentEvent, KeyEvent

from visidroid import VisiDroidFull

from device_manager import DeviceManager, ExternalAction, recover_activity_stack, is_loading_state
from collections import defaultdict, OrderedDict
from targets import initial_knowledge_map


SCRIPT_DIR = os.path.dirname(__file__)
PROFILE_DIR = os.path.join(SCRIPT_DIR, '..', 'resources/personas')

POST_EVENT_WAIT = 1
MAX_STEP = 8000
###### Run for a TASK with --task ###############
## python run_visidroid.py --task "go to the 'recent' tab and open the test1.m4a" --app com.simplemobiletools.filemanager.pro_136 --output_dir ../evaluation/data_new/FileManager --is_emulator --train 3

###### Run many task in an APP with --task_file ########
## python run_visidroid.py --task_file ../tasks/clock/tasks.txt --app com.simplemobiletools.clock_42 --output_dir ../evaluation/data_new/VoiceRecorder --is_emulator --train 3
## python run_visidroid.py --task_file ../tasks/camera/tasks.txt --app camera --output_dir ../evaluation/data_new/camera --is_emulator --train 3
## python run_visidroid.py --task_file ../tasks/musicplayer/tasks.txt --app musicplayer --output_dir ../evaluation/musicplayer/musicplayer --is_emulator --train 3
## python run_visidroid.py --task_file ../tasks/dialer/tasks.txt --app dialer --output_dir ../evaluation/dialer/dialer --is_emulator --train 3
## python run_visidroid.py --task_file ../tasks/calendar/tasks.txt --app calendar --output_dir ../evaluation/calendar/task --is_emulator --train 3
## python run_visidroid.py --task_file ../tasks/note/tasks.txt --app note --output_dir ../evaluation/note/task --is_emulator --train 3

def load_profile(profile_id):
    if not os.path.exists(os.path.join(PROFILE_DIR, f'{profile_id}.txt')):
        raise FileNotFoundError(f'Profile {profile_id} does not exist')

    with open(os.path.join(PROFILE_DIR, f'{profile_id}.txt'), 'r') as f:
        profile_content = f.read().strip()
        
    
    profile = OrderedDict()
    for l in profile_content.split('\n'):
        l = l.strip()
        if l.startswith('-'):
            l = l.removeprefix('-').strip()
            prop = l.split(':')[0].strip()
            val = l.split(':')[1].strip()
            profile[prop] = val
    
    return profile


# @timeout(7200)
def main(device, app, persona, debug=False):
    start_time = time.time()
    agent = VisiDroidFull(output_dir, app=app, persona=persona, debug_mode=debug, device=device)
    device_manager = DeviceManager(device, app, output_dir=output_dir)
    agent.set_current_gui_state(device_manager.current_state)
    need_state_update = False
    print(persona)
    # print(persona.ultimate_goal)
    max_loading_wait = 3
    loading_wait_count = 0
    counter = 0
    while True:
        if persona['train'] is not None:
            if counter >= persona['train']:
                # device.uninstall_app(app)
                # device.disconnect()
                # device.tear_down()
                break

        if persona['evaluate'] is not None:
            if counter >= persona['evaluate']:
                images_id_assert, images_id_final = agent.compare_state()
                if images_id_assert is None:
                    break
                print(f"Images assert: {images_id_assert}")
                print(f"Images final: {images_id_final}")
                with open(os.path.join(output_dir, 'result.txt'), 'w') as f:
                    f.write(images_id_final)
                # device.uninstall_app(app)
                # device.disconnect()
                # device.tear_down()
                break



        if agent.step_count > MAX_STEP:
            print(f'Maximum number of steps reached ({agent.step_count})')
            break

        if agent.step_count % 10 == 0:
            print(f'Time left: {round(((7200 - (time.time() - start_time)) / 60), 2)} min')

        if is_loading_state(device_manager.current_state):
            loading_wait_count += 1

            if loading_wait_count > max_loading_wait:
                print('Loading state persisted for too long. Pressing the back button to go back to the previous state...')
                go_back_event = KeyEvent(name='BACK')
                event_dict = device_manager.send_event_to_device(go_back_event)
                agent.memory.append_to_working_memory(ExternalAction(f'{agent.persona_name} pressed the back button because there was no interactable widgets', [event_dict]), 'ACTION')
                loading_wait_count = 0
                continue
                
            else:
                print('Loading state detected. Waiting for the app to be ready...')
                time.sleep(POST_EVENT_WAIT)
                device_manager.fetch_device_state()
                need_state_update = True
                continue

        if need_state_update:   
            # seems that the loading is done and need to update the state captured right after the action to the recent state
            agent.set_current_gui_state(device_manager.current_state)
            device_manager.add_new_utg_edge()
            need_state_update = False
        # print(f"Screenshot Path: {device_manager.current_state.screenshot_path}")
        action = agent.step()
        agent.save_memory_snapshot()
        
        # Reset activity when reflection is done
        if action == 'Reflection' or action is False or action is True:
            device_manager.fetch_device_state()
            agent.set_current_gui_state(device_manager.current_state)
            
        if persona['train'] is not None or persona['evaluate'] is not None:
            folder = persona['phase']
            print(f"Action: {action}")
            print(f"Folder: {folder}")

            if persona['phase'].startswith('training'):
                phase = 'train'
            else:
                phase = 'evaluate'
            if action is True:
                action = None
                if counter < persona[phase]:
                    train_dir = os.path.join(output_dir, folder, f'{phase}')
                    train_dir = get_unique_output_dir(train_dir)
                    
                    os.makedirs(train_dir, exist_ok=True)
                    with open(os.path.join(train_dir, 'exp_data.json'), 'w') as f:
                        json.dump(agent.exp_data, f, indent=2)

                    if persona['evaluate'] is not None:
                        with open(os.path.join(train_dir, 'screen_description.txt'), 'w') as f:
                            json.dump(agent.screen_description, f, indent=2)

                    import shutil
                    #get finish state
                    source_state = os.path.join(device_manager.current_state.screenshot_path)
                    des_state = os.path.join(train_dir, f'{folder}')
                    shutil.copy(source_state, des_state)

                    counter += 1
            elif action is False and persona['train'] is not None:
                action = None
                if counter < persona[phase]:
                    train_dir = os.path.join(output_dir, folder, f'{phase}')
                    train_dir = get_unique_output_dir(train_dir)
                    os.makedirs(train_dir, exist_ok=True)
                    with open(os.path.join(train_dir, 'exp_data.json'), 'w') as f:
                        json.dump(agent.exp_data, f, indent=2)
                    counter += 1
            elif action is False and persona['evaluate'] is not None:
                #Set action = none to skip the droidbot event
                action = None
                if counter < persona[phase]:
                    train_dir = os.path.join(output_dir, folder, f'{phase}')
                    train_dir = get_unique_output_dir(train_dir)
                    os.makedirs(train_dir, exist_ok=True)
                    with open(os.path.join(train_dir, 'exp_data.json'), 'w') as f:
                        json.dump(agent.exp_data, f, indent=2)
                    counter += 1
        if action is not None:
            event_records = []
            events = action.to_droidbot_event()
            for event in events:
                event_dict = device_manager.send_event_to_device(event, capture_intermediate_state=True, agent=agent)
                event_records.append(event_dict)
            
            action.add_event_records(event_records)

            recover_activity_stack(device_manager, agent)
            agent.set_current_gui_state(device_manager.current_state)
        
        
    


def get_unique_output_dir(base_output_dir):
    output_dir = base_output_dir
    counter = 1

    # Check if the directory exists, and if it does, add a suffix
    while os.path.exists(output_dir):
        output_dir = f"{base_output_dir}_{counter}"
        counter += 1

    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a task-based exploration')
    parser.add_argument('--app', type=str, help='name of the app to be tested', default='AnkiDroid')
    parser.add_argument('--output_dir', type=str, help='path to the output directory', default=None)
    parser.add_argument('--profile_id', type=str, help='name of the persona profile to be used', default='jade')
    parser.add_argument('--task', type=str, help='task to be resolved', default=None)
    parser.add_argument('--task_file', type=str, help='list of tasks to be resolved in a file', default=None)
    parser.add_argument('--train', type=int, help='whether application need to be trained to perform better', default=None)
    parser.add_argument('--evaluate', type=int, help='evaluation phase perform base on rule of training phase', default=None)
    parser.add_argument('--is_emulator', action='store_true', help='whether the device is an emulator or not', default=True)
    parser.add_argument('--debug', action='store_true', help='whether to run the agent in the debug mode or not', default=False)
    args = parser.parse_args()
    
    timestamp = time.strftime("%Y%m%d%H%M%S")


    persona = OrderedDict()
    persona.update(load_profile(args.profile_id))
    assert 'name' in persona, f'The persona profile {args.profile_id} does not have a name'
    persona_name = persona['name']
    #Set up ultimate goal
    if args.task_file is not None:
        ultimate_goal_file = args.task_file
    elif args.task is not None:
        ultimate_goal = f"{args.task}"


    
    if args.train:
        persona['train'] = args.train
        persona['phase'] = 'training_phase'
    else:
        persona['train'] = None

    if args.evaluate:
        persona['evaluate'] = args.evaluate
        persona['phase'] = 'evaluation_phase'
    else:
        persona['evaluate'] = None

    if len(ultimate_goal_file) > 0:
        list_ultimate_goal = []
        with open(ultimate_goal_file, 'r') as file:
            for line in file:
                task = line.strip()
                if task:  # Ensure the line is not empty
                    list_ultimate_goal.append(task)

        for ultimate_goal in list_ultimate_goal:   
            if args.debug:
                output_dir = os.path.join(SCRIPT_DIR, f'../evaluation/data_new/{args.app}/agent_run_debug_{args.profile_id}')
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
            elif args.output_dir is None:
                output_dir = os.path.join(SCRIPT_DIR, f'../evaluation/data_new/{args.app}/agent_run_{args.profile_id}_{timestamp}')
            else:
                output_dir = get_unique_output_dir(args.output_dir)

            device = Device(device_serial='emulator-5554', 
                            output_dir=output_dir, grant_perm=True, is_emulator=args.is_emulator)
            device.set_up()
            device.connect()

            app_path = os.path.join(SCRIPT_DIR, '../target_apps/' + args.app + '.apk')
            app = App(app_path, output_dir=output_dir)
            app_name = app.apk.get_app_name()

            persona.update({
                'ultimate_goal': ultimate_goal,
                'initial_knowledge': f"VisiDroid starts the app {app_name} successfully",
            })

            os.makedirs(output_dir, exist_ok=True)
            with open(f'{output_dir}/exp_info.json', 'w') as f:
                json.dump({
                    'app_name': app_name,
                    'app_path': os.path.abspath(app_path),
                    'device_serial': device.serial,
                    'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                }, f, indent=4)
            print("ULTIMATE GOAL: " + ultimate_goal)
            
            # device.install_app(app)
            device.start_app(app)

            print('Waiting 10 secs for the app to be ready...')
            print('Output directory:', os.path.abspath(output_dir))
            time.sleep(5)
            
            try:
                main(device, app, persona, debug=args.debug)
            except (KeyboardInterrupt, TimeoutError) as e:
                print("Ending the exploration due to a user request or timeout.")
                print(e)
                exit(0)

            except Exception as e:
                print("Ending the exploration due to an unexpected error.")
                print(e)

                raise e



    else:
        persona.update({
            'ultimate_goal': ultimate_goal,
            # 'ultimate_goal': 'check whether the app supports interactions between multiple users', # for QuickChat case study
            'initial_knowledge': initial_knowledge_map(args.app, persona_name, app_name),
        })

        os.makedirs(output_dir, exist_ok=True)
        with open(f'{output_dir}/exp_info.json', 'w') as f:
            json.dump({
                'app_name': app_name,
                'app_path': os.path.abspath(app_path),
                'device_serial': device.serial,
                'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            }, f, indent=4)
        
        device.install_app(app)
        device.start_app(app)

        print('Waiting 10 secs for the app to be ready...')
        print('Output directory:', os.path.abspath(output_dir))
        time.sleep(5)
        
        try:
            main(device, app, persona, debug=args.debug)
        except (KeyboardInterrupt, TimeoutError) as e:
            print("Ending the exploration due to a user request or timeout.")
            print(e)
            device.uninstall_app(app)
            device.disconnect()
            device.tear_down()
            exit(0)

        except Exception as e:
            print("Ending the exploration due to an unexpected error.")
            print(e)
            device.uninstall_app(app)
            device.disconnect()
            device.tear_down()

            raise e
        
    device.uninstall_app(app)
    device.disconnect()
    device.tear_down()
    
