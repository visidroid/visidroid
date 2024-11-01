# Towards Test Generation from Task Description for Mobile Testing with Multi-modal Reasoning

This repository contains the source code and experimental results for the paper "Towards Test Generation from Task Description for Mobile Testing with Multi-modal Reasoning."

## Source Code

The source code can be found in the [src](src) directory.

## Experimental Results

### 1. Research Questions and Ablation Studies

- **RQ1: Generation of Action Sequences**
- **RQ3-5: Ablation Study**

  The experiments for these research questions can be found in the `experiments\rq1-3-4-5` directory. The ground truth data from DroidTasks is located in `experiments\rq1-3-4-5\groundtruth`.

  **Note:** In our evaluation, the ground truth is used for reference only. Since an Android task can be achieved in multiple ways, the generated sequences of actions may require additional steps, such as granting permissions, which are not included in the dataset. We manually double-check the evaluation by running the `experiments\rq1-3-4-5\gui_evaluation.py` file for GUI evaluation.

### 2. Test Generations

- All generated test scripts are zipped in `experiments\rq2-test-gen\test_scripts.zip`.
- Test script runtime evaluations are recorded in `experiments\rq2-test-gen\visidroid_evals.csv`, along with reasons for any unexecutable test scripts.

## Experimental Logs

### Visidroid

- **Full Experiment Log:** [Download](https://drive.google.com/file/d/18Ngdk6PkqjsmBQJQILFlp4rRnPOtE_0d/view?usp=drive_link)
- **Memory Ablation Log:** [Download](https://drive.google.com/file/d/1NrXmXDjKfBk3BBgPhv2FrqhAFYnJBoBK/view?usp=drive_link)
- **Vision Ablation Log:** [Download](https://drive.google.com/file/d/1_wxTo2JAMbX6TTBkR_XPMMUDams9ZfpY/view?usp=drive_link)

### Baselines

- **Guardian:** [Download](https://drive.google.com/file/d/1hb8cfiDvALWW5rssuHyhdcbMM4BMryu_/view?usp=drive_link)
- **Droidagent:** [Download](https://drive.google.com/file/d/1YQn70w3vl6NYQQxAfD24xUdjFv-s24xx/view?usp=drive_link)
- **Autodroid:** We reused their replication package, available [here](https://github.com/autodroid-sys/artifacts/tree/main).

## Acknowledgments

We extend our special thanks to the DroidTask team for releasing their dataset and ground truths.
