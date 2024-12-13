from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.hooks.base_hook import BaseHook
from airflow.models import Variable
from datetime import datetime, timedelta
import medium_api as medium
import json

default_args = {
    'owner': '',
    'start_date': datetime(2024, 2, 23),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    '',
    default_args=default_args,
    schedule=None,
    tags=["medium_api_calls"]
)

# Replace with your own values
bucket_name = ''
json_file_path = ''
google_cloud_storage_conn_id = ''


def get_medium_data(**kwargs):
    """
    DAG task to retrieve data from the Medium API, upload it to GCS,
    and push file paths to XCom.

    This function fetches data from the Medium API, including writer
    information, follower data, and writer IDs. It then uploads this
    data to GCS and pushes the file paths to XCom for downstream tasks.

    :param kwargs: Context passed by Airflow
    """
    # Access API key
    API_KEY = Variable.get('API_KEY')
    HEADERS = {'X-RapidAPI-Key': API_KEY,
               'X-RapidAPI-Host': 'medium2.p.rapidapi.com'}
    ti = kwargs['ti']
    # retrieve data using Medium API
    writer_ids = medium.check_top_writers(headers=HEADERS)
    writer_list = medium.get_all_writer_info(writer_ids=writer_ids)
    follower_data = medium.get_follower_table(writer_list)

    # Convert data to JSON strings
    writer_id_json = json.dumps(writer_ids)
    writer_json = json.dumps(writer_list)
    follower_json = json.dumps(follower_data)

    # Upload data to GCS
    gcs_hook = GCSHook(google_cloud_storage_conn_id)
    gcs_hook.upload(bucket_name=bucket_name,
                    object_name='writer_ids.json',
                    data=writer_id_json)
    gcs_hook.upload(bucket_name=bucket_name,
                    object_name='writer_information.json',
                    data=writer_json)
    gcs_hook.upload(bucket_name=bucket_name,
                    object_name='follower_information.json',
                    data=follower_json)

    # Push file paths to XCom for downstream tasks
    ti.xcom_push(key='medium_writer_file',
                 value='writer_information.json')
    ti.xcom_push(key='medium_follower_file',
                 value='follower_information.json')


# Python function to import data from GCS to MongoDB
def uploadtomongo(**kwargs):
    """
    DAG task to download data from GCS and upload it to MongoDB.

    This function downloads writer and follower data from GCS, having pulled
    the file paths from XCom, then uploads the data to MongoDB.

    :param kwargs: Context passed by Airflow
    """
    try:
        ti = kwargs['ti']
        # Retrieve file paths from XCom
        writer_file = ti.xcom_pull(key='medium_writer_file',
                                   task_ids='medium_api_task')
        follower_file = ti.xcom_pull(key='medium_follower_file',
                                     task_ids='medium_api_task')

        # Download data from GCS
        gcs_hook = GCSHook(google_cloud_storage_conn_id)
        writer_content = gcs_hook.download(bucket_name=bucket_name,
                                           object_name=writer_file)
        writer_content = writer_content.decode('utf-8')
        follower_content = gcs_hook.download(bucket_name=bucket_name,
                                             object_name=follower_file)
        follower_content = follower_content.decode('utf-8')

        # Convert data to Python objects
        writer_data = json.loads(writer_content)
        follower_data = json.loads(follower_content)

        # upload data to MongoDB
        hook = MongoHook(mongo_conn_id='mongo_default')
        client = hook.get_conn()
        db = client.medium_database
        writer_collection = db.writer_raw
        print(f"Connected to MongoDB - {client.server_info()}")
        writer_collection.insert_many(writer_data)
        follower_collection = db.follower_raw
        follower_collection.insert_many(follower_data)
    except Exception as e:
        print(f"Error connecting to MongoDB -- {e}")


medium_api_task = PythonOperator(
    task_id='medium_api_task',
    python_callable=get_medium_data,
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag
)

upload_to_mongodb = PythonOperator(
    task_id='upload-mongodb',
    python_callable=uploadtomongo,
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag
)

medium_api_task >> upload_to_mongodb
