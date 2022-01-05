import os
import subprocess

from TrainManager import TrainingManager, TrainChecker


def system_check():
    with open("/home/mauser/queue.dat", 'r') as f:
        if os.path.getsize("/content/queue.dat") == 0:
            print("Nothing left in the queue")
            return
        lines = f.readlines()
        next_in_queue = lines[0]
        split = next_in_queue.split(" ")
        artist = split[0]
        style = split[1]
        zip = split[2]
        retrain = False if split[3] == "False" else True
        status = split[4]

    train_manager = TrainingManager(artist, style, retrain=retrain, working_path="/home/mauser", kimg=5000, gpus=8)
    train_checker = TrainChecker(train_manager)
    if status == "new\n" or status == "new":
        if retrain:
            train_manager.combine_sets(zip)
        else:
            train_manager.download_new_style()
        train_manager.prepare_images(512)
        train_manager.train_fn(kimg=5000, snap=100)
        lines[0] = f"{artist} {style} {zip} {retrain} running"+"\n"
        with open("/home/mauser/queue.dat", 'w') as f:
            f.writelines(lines)
    else:
        check_value = train_checker.check()  # 1 - Restarting; 2 - Job Finished; 3 - Job is Healthy
        if check_value == 2:
            train_manager.switch_models()
            with open("/home/mauser/queue.dat", 'r+') as f:
                firstLine = f.readline()  # read the first line and throw it out
                data = f.read()  # read the rest
                f.seek(0)  # set the cursor to the top of the file
                f.write(data)  # write the data back
                f.truncate()  # set the file size to the current size
                # Needs to be tested
            system_check()
    return


if __name__ == "__main__":
    system_check()
