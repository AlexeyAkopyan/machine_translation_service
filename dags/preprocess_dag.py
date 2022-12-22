from datetime import datetime

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.decorators import task
from airflow.utils.edgemodifier import Label

# Docker library from PIP
import docker

# Simple DAG
with DAG(
    "process_train", 
    start_date=datetime(2015, 2, 2), 
    catchup=False, 
    tags=['nmt']
) as dag:


    @task(task_id='preprocess')
    def run_preprocess(**kwargs):

        # get the docker params from the environment
        client = docker.from_env()
          
            
        # run the container
        command = (
            "python preprocess.py --train-src data/raw/train.ru_en.ru "
            "--train-trg data/raw/train.ru_en.en "
            "--val-src data/raw/valid.ru_en.ru "
            "--val-trg data/raw/valid.ru_en.en "
            "--test-src data/raw/test.ru_en.ru "
            "--test-trg data/raw/test.ru_en.en "
            "--src-lang ru "
            "--trg-lang en "
            "--src-vocab-size 4000 "
            "--trg-vocab-size 4000 "
            "--save-data-dir ./data/processed/ "
            "--max-seq-len 128 "
            "--src-tokenizer-path ./weights_models/ru_tokenizer.model "
            "--trg-tokenizer-path ./weights_models/en_tokenizer.model")

        response = client.containers.run(

             # The container you wish to call
             'nmt_service:latest',

             # The command to run inside the container
             command,

             stdout=True,
             stderr=True,
             tty=True,
             detach=True, 
             remove=True,

             # Passing the GPU access
             device_requests=[
                 docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])
             ], 
             
             # Give the proper system volume mount point
             volumes=[
                 '/home/iref/Repos/machine_translation_sercive/data:/nmt_service/data',
                 '/home/iref/Repos/machine_translation_sercive/weights_models:/nmt_service/weights_models'
             ]
        )

        output = response.attach(stdout=True, stream=True, logs=True)
        for line in output:
            print(line.decode())

        return str(response)


    
    @task(task_id='train')
    def run_train(**kwargs):

        # get the docker params from the environment
        client = docker.from_env()
          
            
        # run the container
        command = (
            "python train.py --train-path ./data/processed/train.ru_en.pkl "
            "--val-path ./data/processed/val.ru_en.pkl "
            "--embedding-size 512 "
            "--n-heads 8 "
            "--n-layers 3 "
            "--dropout 0.1 "
            "--lr 0.0002 "
            "--max-epochs 2 "
            "--batch-size 128 "
            "--src-vocab-size 10000 "
            "--trg-vocab-size 10000 "
            "--src-lang ru "
            "--trg-lang en "
            "--max-seq-len 128 "
            "--display-freq 100 "
            "--model-path ./weights_models/transformer.pt "
            "--use-cuda True"
        )

        response = client.containers.run(

             # The container you wish to call
             'nmt_service:latest',

             # The command to run inside the container
             command,

             stdout=True,
             stderr=True,
             tty=True,
             detach=True, 
             remove=True,

             # Passing the GPU access
             device_requests=[
                 docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])
             ], 
             
             # Give the proper system volume mount point
             volumes=[
                 '/home/iref/Repos/machine_translation_sercive/data:/nmt_service/data',
                 '/home/iref/Repos/machine_translation_sercive/weights_models:/nmt_service/weights_models'
             ]
        )

        output = response.attach(stdout=True, stream=True, logs=True)
        for line in output:
            print(line.decode())

        return str(response)


    run_preprocess_task = run_preprocess()
    run_train_task = run_train()


    # Dummy functions
    #start = DummyOperator(task_id='start')
    #end   = DummyOperator(task_id='end')


    # Create a simple workflow
    run_preprocess_task >> run_train_task