# Towards Test Generation from Task Description for Mobile Testing with Multi-modal Reasoning

This repository contains the source code and experimental results for the paper "Towards Test Generation from Task Description for Mobile Testing with Multi-modal Reasoning."


## Source Code

The source code is available in the [src](src) directory.

## Setup

## Clone & Install Dependencies

```bash
$ git clone --recurse-submodule https://github.com/visidroid/visidroid
$ cd src/visidroid/droidbot
$ pip install -e . # Install droidbot
```

### OpenAI Requirements

Our tool, Visidroid, requires a multi-modal setup. Please ensure that your API key allows access to "GPT-4o" and "GPT-4". Create an `.env` file under `src/visidroid` with the following content:

```plaintext
OPENAI_API_KEY=<yourkey>
```

### Hardware Requirements

This setup uses the Android emulator from Android Studio, configured as Pixel 3a device running Android 14.0 (UpsideDownCake, API level 34). The emulator ran on a 64-bit Windows 11 machine with:

- **CPU**: AMD Ryzen 7 7840HS (8 cores)
- **Memory**: 32 GB RAM

Lower hardware settings may work but have not been tested for smooth performance.

### APK Files

The zip file containing 12 APKs for the apps used in our experiment can be downloaded from [Download](https://drive.google.com/file/d/1Q3OZwROO7K2Zm5AhFZzrdX82UPUkOBN7/view?usp=drive_link). Please extract it into `src/visidroid/target_apps`.


## Execution

### Sequence of Actions Generation

To generate a sequence of actions, use the `run_visidroid.py` script. Here is an example command:

Run the script with the following command:

```bash
python run_visidroid.py --task_file <path_to_task_file> --app <app_name> --output_dir <output_directory> --is_emulator --train <train_level>
```

### Example

```bash
python run_visidroid.py --task_file ../tasks/clock/tasks.txt --app com.simplemobiletools.clock_42 --output_dir ../evaluation/data_new/VoiceRecorder --is_emulator --train 3
```

### Arguments

- `--task_file`: Path to file containing tasks.
- `--app`: App package name (e.g., `com.simplemobiletools.clock_42`).
- `--output_dir`: Directory for output files.
- `--is_emulator`: Indicates the device is an emulator.
- `--train`: How many times you want you train.

For more options, check the script's argument parser.

### Test Generation

For test generation, use the `make_script.py` script with the following command:

```bash
python make_script.py --project <project_name> --package_name <package_name> --result_dir <result_directory>
```

### Example

```bash
python make_script.py --project VoiceRecorder --package_name com.simplemobiletools.voicerecorder --result_dir ../evaluation/data_new/Contacts_26/training_phase/train
```

### Arguments

- `--project`: Name of the project (e.g., `VoiceRecorder`).
- `--package_name`: Package name of the app to test (e.g., `com.simplemobiletools.voicerecorder`).
- `--result_dir`: Output directory of the action sequence generation.


## Experimental Results

### 1. Generation of Action Sequences and Ablation Study

- **Research Questions (RQ1, RQ3-5):** The experiments related to the generation of action sequences and the ablation study can be found in the [experiments/rq1-3-4-5](experiments/rq1-3-4-5) directory.
- **Ground Truth from DroidTasks:** The ground truth data is located in [experiments/rq1-3-4-5/groundtruth](experiments/rq1-3-4-5/groundtruth).

Please note that in our evaluation, we use the ground truth for reference only. Since an Android task can be achieved in multiple ways, the generated sequences of actions may require granting permissions for Android apps, which are not included in the dataset. We manually perform a double-check on the evaluation by running the [experiments/rq1-3-4-5/gui_evaluation.py](experiments/rq1-3-4-5/gui_evaluation.py) file for GUI evaluation.

### 2. Test Generations

- **Generated Test Scripts:** All generated test scripts are zipped in [experiments/rq2-test-gen/test_scripts.zip](experiments/rq2-test-gen/test_scripts.zip).
- **Test Script Runtime Evaluation:** The runtime evaluations of the test scripts are recorded in [experiments/rq2-test-gen/visidroid_evals.csv](experiments/rq2-test-gen/visidroid_evals.csv), along with some reasons for unexecutable test scripts.

## Experimental Logs (Prompts and Recorded App States)

### Visidroid

- **Full Model:** [Download](https://drive.google.com/file/d/18Ngdk6PkqjsmBQJQILFlp4rRnPOtE_0d/view?usp=drive_link)
- **Memory Ablation:** [Download](https://drive.google.com/file/d/1NrXmXDjKfBk3BBgPhv2FrqhAFYnJBoBK/view?usp=drive_link)
- **Vision Ablation:** [Download](https://drive.google.com/file/d/1_wxTo2JAMbX6TTBkR_XPMMUDams9ZfpY/view?usp=drive_link)

### Baselines

- **Guardian:** [Download](https://drive.google.com/file/d/1hb8cfiDvALWW5rssuHyhdcbMM4BMryu_/view?usp=drive_link)
- **Droidagent:** [Download](https://drive.google.com/file/d/1YQn70w3vl6NYQQxAfD24xUdjFv-s24xx/view?usp=drive_link)
- **Autodroid:** We reused their replication package, available at [GitHub](https://github.com/autodroid-sys/artifacts/tree/main).

## Acknowledgments

We extend our special thanks to the DroidTask team for releasing their dataset and ground truths. We also thank the [DroidAgent](https://github.com/coinse/droidagent) team for sharing their code, which we adapted for use in VisiDroid.

We would also like to thank the teams behind [Autodroid](https://github.com/MobileLLM/AutoDroid) , [Guardian](https://github.com/PKU-ASE-RISE/Guardian), and [DroidAgent](https://github.com/coinse/droidagent) for sharing their code, which we used in our experiments.