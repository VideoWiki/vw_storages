# tasks.py

# tasks.py

from celery import shared_task
from celery.result import AsyncResult
from .celery import app as celery_app
import os
import requests
from urllib.parse import urlparse
from django.core.files.temp import NamedTemporaryFile
import base64

@shared_task
def upload_file_to_server(url, data, headers, file_path, file_name):
    with open(file_path, 'rb') as file:
        files = {'files': (file_name, file)}
        response = requests.post(url, data=data, headers=headers, files=files)

    # Check if the upload was successful (you can adjust the condition as needed)
    if response.status_code == 200:
        # Delete the file after successful upload
        os.remove(file_path)
        return response.text
    else:
        # Handle the case where the upload was not successful
        return f"File upload failed with status code {response.status_code}: {response.text}"


@shared_task
def check_upload_status(task_id):
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
    }

@shared_task
def download_file_and_encode(url, cookie, filename, podname):
    url = url + "v1/file/download"
    headers = {
        'Cookie': cookie
    }
    files = {
        'filePath': (None, filename),
        'podName': (None, podname)
    }

    response = requests.post(url, headers=headers, files=files, stream=True)
        
    if response.status_code == 200:
        content = response.content
        base64_content = base64.b64encode(content).decode('utf-8')
        return {"file_content_base64": base64_content}
    else:
        return {"error": "File download failed"}
