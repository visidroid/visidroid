#!/bin/bash

#./run.sh Task folder 

echo $1

APP_NAME=$1
APP_PACKAGE=$2
TASK_DIR=$3

tasks=()
tasks_path="../tasks/$APP_NAME/tasks.txt"
MAX_RETRIES=3
if [[ -f "$tasks_path" ]]; then
    # Read each line of the file and append it to the tasks array
    while IFS= read -r line; do
        tasks+=("$line")
    done < "$tasks_path"
else
    echo "File not found: $file"
    exit 1
fi
# Function to run the command
run_training_command() {
    # Your command goes here
    python run_visidroid.py --task "$task" --app $APP_PACKAGE --output_dir ../evaluation/data_new/$APP_NAME --is_emulator --train 3
}

run_evaluate_command() {
    # Your command goes here
    python run_visidroid.py --task "$task" --app $APP_PACKAGE --output_dir ../evaluation/data_new/$APP_NAME --is_emulator --evaluate 3
}


for task in "${tasks[@]}"; do
    echo "###############################"
    echo "###############################"
    echo "Task Working: $task"
    echo "###############################"
    echo "###############################"
    while true; do

        if run_training_command; then
            # Command succeeded, break out of the loop
            break
        else
            # Command failed, increment the retry count
            ((retry_count++))
            if [ $retry_count -ge $MAX_RETRIES ]; then
                echo "Maximum number of retries reached. Exiting."
                exit 1
            fi
            echo "Command failed. Retrying in 5 seconds..."
            sleep 5
        fi
    done
done

for task in "${tasks[@]}"; do
    echo "###############################"
    echo "###############################"
    echo "Task Working: $task"
    echo "###############################"
    echo "###############################"
    while true; do

        if run_evaluate_command; then
            # Command succeeded, break out of the loop
            break
        else
            # Command failed, increment the retry count
            ((retry_count++))
            if [ $retry_count -ge $MAX_RETRIES ]; then
                echo "Maximum number of retries reached. Exiting."
                exit 1
            fi
            echo "Command failed. Retrying in 5 seconds..."
            sleep 5
        fi
    done
done
# python run_visidroid.py --task "Create a new contact Stephen Bob, mobile number 12345678900" --app com.simplemobiletools.contacts.pro_107 --output_dir ../evaluation/data_new/$APP_NAME --is_emulator --train 3

# python run_visidroid.py --task "Create a new contact Stephen Bob, mobile number 12345678900" --app com.simplemobiletools.contacts.pro_107 --output_dir ../evaluation/data_new/$APP_NAME --is_emulator --evaluate 3
sleep 15s