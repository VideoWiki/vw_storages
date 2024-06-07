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
from django.conf import settings
import uuid


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


@shared_task
def download_and_upload(video_url):
    file_name = f"{uuid.uuid4()}.m4v"
    download_path = os.path.join(settings.MEDIA_ROOT, file_name)
    print(file_name, video_url, download_path)

    # Download the video from the URL and save it temporarily
    response = requests.get(video_url)
    with open(download_path, 'wb') as file:
        file.write(response.content)

    # Upload the downloaded file to the Swarm API
    url = 'https://dev.api.cast.video.wiki/bzz?name=' + download_path
    headers = {
        'swarm-postage-batch-id': '05ad9f1dfc0f4c55e04c077d9d3298e13a10b00b052633938f6627327b3e9ca5',
        'Content-Type': 'text/plain'
    }
    with open(download_path, 'rb') as file:
        upload_response = requests.post(url, headers=headers, data=file)

    # Remove the downloaded file after upload
    os.remove(download_path)

    return upload_response.json(), upload_response.status_code
