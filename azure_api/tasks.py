from celery import shared_task
from azure.storage.blob import BlobClient
import redis, os
import requests
redis_client = redis.Redis(host='localhost', port=6379, db=0)


@shared_task
def upload_file_task(connect_str, container_name, blob_name, file_path, task_id):
    # Define the blob name
    blob_name = blob_name

    # Create a BlobClient object for the new blob
    blob_client = BlobClient.from_connection_string(connect_str, container_name=container_name, blob_name=blob_name)

    file_urls = []
    try:
        # Upload the file to Azure Blob Storage
        with open(file_path, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)

        # Return the URL of the uploaded file
        file_url = f"https://{blob_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        file_urls.append(file_url)

    except Exception as e:
        # If an error occurs, raise an exception with the error message
        raise Exception(str(e))

    finally:
        # Remove the local file
        os.remove(file_path)

    if file_urls:
        redis_client.set(task_id, file_urls[0])

        return file_urls[0]


@shared_task
def upload_file_url_task(connect_str, container_name, blob_name, file_path, task_id, url):
    # Define the blob name
    blob_name = blob_name
    r = requests.get(url, stream=True)
    with open(file_path, 'wb') as f:
        f.write(r.content)
    # Create a BlobClient object for the new blob
    blob_client = BlobClient.from_connection_string(connect_str, container_name=container_name, blob_name=blob_name)

    file_urls = []
    try:
        # Upload the file to Azure Blob Storage
        with open(file_path, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)

        # Return the URL of the uploaded file
        file_url = f"https://{blob_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        file_urls.append(file_url)

    except Exception as e:
        # If an error occurs, raise an exception with the error message
        raise Exception(str(e))

    finally:
        # Remove the local file
        os.remove(file_path)

    if file_urls:
        redis_client.set(task_id, file_urls[0])

        return file_urls[0]







