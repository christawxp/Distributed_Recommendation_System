from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
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
    tags=["recommender"]
)

# Replace with your own values
bucket_name = ''
json_file_path = ''
google_cloud_storage_conn_id = ''

def upload_to_mongo_follower_data(file_content_list):
    try:
        # ti = kwargs['ti']
        # gcs_data = ti.xcom_pull(key='gcs_data', task_ids='get-content-task')

        hook = MongoHook(mongo_conn_id='mongo_default')
        client = hook.get_conn()
        db = client.medium_database
        collection = db.follower_collection

        followers_id_mapping = {}
        print(file_content_list)
        # Iterate through each dictionary in the list
        for entry in file_content_list:
            # Extract 'id' and 'followers' from the dictionary
            entry_id = entry.get('id')
            followers = entry.get('followers', set())

            # Update the mapping in the new dictionary
            for follower in followers:
                if follower not in followers_id_mapping:
                    followers_id_mapping[follower] = {entry_id}
                else:
                    followers_id_mapping[follower].add(entry_id)

            # Assuming 'id' is a unique identifier, replace it with the actual unique key in your data
            unique_key = {'id': entry_id}

            # Update each entry individually in MongoDB
            collection.update_one(unique_key, {'$set': entry}, upsert=True)

    except Exception as e:
        print(f"Error connecting to MongoDB -- {e}")

def upload_to_mongo_articles_data(file_content_list):
    try:
        # ti = kwargs['ti']
        # gcs_data = ti.xcom_pull(key='gcs_data', task_ids='get-content-task')

        hook = MongoHook(mongo_conn_id='mongo_default')
        client = hook.get_conn()
        db = client.medium_database
        collection = db.article_collection

        print(file_content_list)
        for entry in file_content_list:
            # Assuming 'articles' is the key for the list of articles in each entry
            articles = entry.get('articles', [])

            # Assuming 'entry_id' is a unique identifier for each entry
            entry_id = entry.get('id')

            # Prepare a list to store the articles for the current entry
            articles_list = []

            for article in articles:
                # Assuming 'article_id' is a unique identifier for each article
                article_id = article.get('id')

                # Append the article to the list
                articles_list.append({'entry_id': entry_id, 'article_id': article_id, 'article_data': article})

                

            # Insert or update the entire list of articles for the current entry
            unique_entry_key = {'entry_id': entry_id}
            collection.update_one(unique_entry_key, {'$set': {'articles': articles_list}}, upsert=True)

    except Exception as e:
        print(f"Error connecting to MongoDB -- {e}")

def upload_to_mongo_writer_data(file_content_list):
    try:
        # ti = kwargs['ti']
        # gcs_data = ti.xcom_pull(key='gcs_data', task_ids='get-content-task')

        hook = MongoHook(mongo_conn_id='mongo_default')
        client = hook.get_conn()
        db = client.medium_database
        collection = db.writer_collection

        print(file_content_list)
        for entry in file_content_list:
            # Remove 'followers' and 'articles' keys from each entry
            entry.pop('followers', None)
            entry.pop('articles', None)

            # Assuming 'id' is a unique identifier, replace it with the actual unique key in your data
            unique_key = {'id': entry['id']}

            # Update each entry individually in MongoDB
            collection.update_one(unique_key, {'$set': entry}, upsert=True)

    except Exception as e:
        print(f"Error connecting to MongoDB -- {e}")

def get_gcs_file_content(**kwargs):
    ti = kwargs['ti']
    gcs_hook = GCSHook(google_cloud_storage_conn_id)
    file_content = gcs_hook.download(bucket_name=bucket_name, object_name=json_file_path)

    try:
        # Attempt to decode the JSON-encoded string into a Python object (list)
        try:
            file_content_list = json.loads(file_content.decode('utf-8'))
        except json.JSONDecodeError:
            print("Content is not a valid JSON array. Trying to interpret as a string.")
            # If decoding as a list fails, try interpreting the content as a string
            file_content_str = file_content.decode('utf-8')
            # Remove the logging information at the beginning
            json_start_index = file_content_str.find("[")
            if json_start_index != -1:
                file_content_str = file_content_str[json_start_index:]
            file_content_list = json.loads(file_content_str)
        
        # Log the content for debugging
        print(f"Decoded Content: {file_content_list}")

        follower_data = upload_to_mongo_follower_data(file_content_list)
        articles_data = upload_to_mongo_articles_data(file_content_list)
        writer_data = upload_to_mongo_writer_data(file_content_list)

        # Push the processed data to XCom
        ti.xcom_push(key='gcs_data_follower', value=follower_data)
        ti.xcom_push(key='gcs_data_article', value=articles_data)
        ti.xcom_push(key='gcs_data_writer', value=writer_data)

    except Exception as e:
        print(f"Error processing content: {e}")


def uploadtomongo(**kwargs):
    try:
        ti = kwargs['ti']
        gcs_data = ti.xcom_pull(key='gcs_data', task_ids='get-content-task')
        d = json.loads(gcs_data)
        hook = MongoHook(mongo_conn_id='mongo_default')
        client = hook.get_conn()
        db = client.medium_database
        test_collection = db.test_collection
        print(f"Connected to MongoDB - {client.server_info()}")
        print(d)
        test_collection.insert_one(d)
    except Exception as e:
        print(f"Error connecting to MongoDB -- {e}")


get_file_gcs_task = PythonOperator(
    task_id='get-content-task',
    python_callable=get_gcs_file_content,
    provide_context=True,
    execution_timeout=timedelta(minutes=30),
    dag=dag
)

upload_to_mongodb = PythonOperator(
    task_id='upload-to-mongodb',
    python_callable=uploadtomongo,
    provide_context=True,  # Pass context to the function
    execution_timeout=timedelta(minutes=30),
    dag=dag
)

get_file_gcs_task >> upload_to_mongodb
