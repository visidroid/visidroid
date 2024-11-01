VisiDroid source code

1. setup

OpenAI requirements
Our visidroid requires multi-modal setup, therefore please make sure that your API key allow "GPT-4o" and "GPT-4"
create an .env file under this directory
with OPENAI_API_KEY=<yourkey>


Hardware requirements:

Hardware. We set up a controlled environment using the Android emulator that comes with
Android Studio. The emulator was configured to mimic a Pixel 3a device running the latest Android
version when this paper was written, Android 14.0 (UpsideDownCake API level 34). The emulator
ran on a 64-bit Windows 11 machine with an R7-7840HS CPU (8 cores) and 32GB memory.

We do not sure that the lower setting can run smoothly

APK files
The zip for 12 apks for apps in our experiement can be downloaded from ...
Please extract it into "src\visidroid\target_apps"




### Clone & Install Dependencies
```bash
$ git clone --recurse-submodule https://github.com/visidroid/visidroid
$ cd src/visidroid/droidbot
$ pip install -e . # install droidbot
$ cd ..
$ pip install -r requirements.txt
$ pip install -e . # install visidroid
```


2. execution

For sequence of actions generation 
[write execution instruction for this] run_visidroid.py

"    parser = argparse.ArgumentParser(description='Run a task-based exploration')
    parser.add_argument('--app', type=str, help='name of the app to be tested', default='AnkiDroid')
    parser.add_argument('--output_dir', type=str, help='path to the output directory', default=None)
    parser.add_argument('--profile_id', type=str, help='name of the persona profile to be used', default='jade')
    parser.add_argument('--task', type=str, help='task to be resolved', default=None)
    parser.add_argument('--task_file', type=str, help='list of tasks to be resolved in a file', default=None)
    parser.add_argument('--train', type=int, help='whether application need to be trained to perform better', default=None)
    parser.add_argument('--evaluate', type=int, help='evaluation phase perform base on rule of training phase', default=None)
    parser.add_argument('--is_emulator', action='store_true', help='whether the device is an emulator or not', default=True)
    parser.add_argument('--debug', action='store_true', help='whether to run the agent in the debug mode or not', default=False)
    parser.add_argument('--device_serial', type=str, help='serial number of the device to be used', default="emulator-5554")
"

For test generation

# python make_script.py --project VoiceRecorder --package_name com.simplemobiletools.voicerecorder --result_dir ../evaluation/data_new/Contacts_26/training_phase/train
