# Towards Test Generation from Task Description for Mobile Testing with Multi-modal Reasoning

This repository contains the source code and experimental results for the paper "Towards Test Generation from Task Description for Mobile Testing with Multi-modal Reasoning."

## Source Code

The source code is available in the [src](src) directory.

## Experimental Results

### 1. Generation of Action Sequences and Ablation Study

- **Research Questions (RQ1, RQ3-5):** The experiments related to the generation of action sequences and the ablation study can be found in the [experiments/rq1-3-4-5](experiments/rq1-3-4-5) directory.
- **Ground Truth from DroidTasks:** The ground truth data is located in [experiments/rq1-3-4-5/groundtruth](experiments/rq1-3-4-5/groundtruth).

Please note that in our evaluation, we use the ground truth for reference only. Since an Android task can be achieved in multiple ways, the generated sequences of actions may require granting permissions for Android apps, which are not included in the dataset. We manually perform a double-check on the evaluation by running the [experiments/rq1-3-4-5/gui_evaluation.py](experiments/rq1-3-4-5/gui_evaluation.py) file for GUI evaluation.

### 2. Test Generations

- **Generated Test Scripts:** All generated test scripts are zipped in [experiments/rq2-test-gen/test_scripts.zip](experiments/rq2-test-gen/test_scripts.zip).
- **Test Script Runtime Evaluation:** The runtime evaluations of the test scripts are recorded in [experiments/rq2-test-gen/visidroid_evals.csv](experiments/rq2-test-gen/visidroid_evals.csv), along with some reasons for unexecutable test scripts.

## Experimental Logs

### Visidroid

- **Full Log:** [Download](https://drive.google.com/file/d/18Ngdk6PkqjsmBQJQILFlp4rRnPOtE_0d/view?usp=drive_link)
- **Memory Ablation:** [Download](https://drive.google.com/file/d/1NrXmXDjKfBk3BBgPhv2FrqhAFYnJBoBK/view?usp=drive_link)
- **Vision Ablation:** [Download](https://drive.google.com/file/d/1_wxTo2JAMbX6TTBkR_XPMMUDams9ZfpY/view?usp=drive_link)

### Baselines

- **Guardian:** [Download](https://drive.google.com/file/d/1hb8cfiDvALWW5rssuHyhdcbMM4BMryu_/view?usp=drive_link)
- **Droidagent:** [Download](https://drive.google.com/file/d/1YQn70w3vl6NYQQxAfD24xUdjFv-s24xx/view?usp=drive_link)
- **Autodroid:** We reused their replication package, available at [GitHub](https://github.com/autodroid-sys/artifacts/tree/main).

## Acknowledgments

We extend our special thanks to the DroidTask team for releasing their dataset and ground truths.