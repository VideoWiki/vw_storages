# views.py
import json 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.temp import NamedTemporaryFile
from urllib.parse import urlparse
from .tasks import upload_file_to_server, check_upload_status, download_file_and_encode
import os
import requests
from subprocess import PIPE, Popen
from dotenv import load_dotenv
from vw_storages.settings import BASE_DIR
from django.http import JsonResponse, HttpResponse
from .tasks import download_and_upload
from celery.result import AsyncResult
from .tasks import upload_video_task, download_video_task
from swarm.celery import app  # Import the Celery app
import base64

load_dotenv()
swarm_url = os.environ.get('SWARM_URL')


class FileUploadAPI(APIView):
    def post(self, request):
        video_url = request.data.get('video_url')
        cookie = request.data.get('cookie')
        username = request.data.get('username')

        if not (video_url and cookie and username):
            return Response({"error": "Video URL, cookie, and username are required."}, status=status.HTTP_400_BAD_REQUEST)

        url = f'{swarm_url}v1/file/upload'
        headers = {
            'Cookie': cookie
        }
        data = {
            'dirPath': f'/{username}',
            'podName': username,
            'blockSize': '1Mb',
        }

        parsed_url = urlparse(video_url)
        file_name = os.path.basename(parsed_url.path)
        download_path = os.path.join(BASE_DIR, "media/", file_name)
        response = requests.get(video_url)
        # Download the video from the URL and save it temporarily
        with open(download_path, 'wb') as file:
                file.write(response.content)
        print(download_path + file_name)

        def cmdline(command):
            process = Popen(
                args=command,
                stdout=PIPE,
                shell=True,
                universal_newlines=False
            )
            return process.communicate()[0]

        output = cmdline(f"node swarm/index.js {download_path}")

        decoded_output = output.decode('utf-8')
        # Call the Celery task for file upload
        upload_task = upload_file_to_server.delay(url, data=data, headers=headers, file_path=download_path, file_name=file_name)

        return Response({"message": "File upload has been initiated.", "task_id": upload_task.id, "filedata": decoded_output}, status=status.HTTP_202_ACCEPTED)




class FileUploadStatusAPI(APIView):
    def get(self, request, task_id):
        status_info = check_upload_status(task_id)
        return Response(status_info, status=status.HTTP_200_OK)

class FileDownloadAPI(APIView):
    def post(self, request, *args, **kwargs):
        cookie = request.data['cookie']
        filename = request.data['filename']
        podname = request.data['podname']

        if not (cookie and filename and podname):
            return Response({"error": "Cookie, filename, and podname are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Call the Celery task for file download and encoding
        task = download_file_and_encode.delay(swarm_url, cookie, filename, podname)
        
        return Response({"message": "File download has been initiated.", "task_id": task.id}, status=status.HTTP_202_ACCEPTED)

class FileDownloadStatusAPI(APIView):
    def get(self, request, task_id):
        task_result = download_file_and_encode.AsyncResult(task_id)
        if task_result.ready():
            result = task_result.result
            if 'file_content_base64' in result:
                base64_content = result['file_content_base64']
                return Response(
                    {"file_content_base64": base64_content},
                    content_type='application/json',
                    status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"status": "Task is still in progress."}, status=status.HTTP_202_ACCEPTED)


#SIA


class VideoUploadViewSIA(APIView):
    def post(self, request, *args, **kwargs):

        # Download file contents as binary
        file_url = request.data['file_url']
        parsed_url = urlparse(file_url)
        filename = parsed_url.path.split("/")[-1]
        if file_url.startswith("https://live1.decast.live"):
            parts = parsed_url.path.split("/")
            # Construct the filename by replacing "/" with "-" in the desired part
            filename = parts[3] + ".m4v"
            print(filename)
        url = f"https://storage.sia.video.wiki/api/worker/objects/videowiki/{filename}"

        resp = requests.get(file_url)
        binary_data = resp.content

        headers = {
            'Content-Type': 'video/webm',
            'Authorization': 'Basic OnBhc3N3b3Jk'
        }

        response = requests.put(url, headers=headers, data=binary_data)
        print(response, response.text)

        return Response({"filename":filename}, status=response.status_code)


class VideoDownloadViewSIA(APIView):
    def get(self, request, *args, **kwargs):
        file_name = request.GET.get('file_name')

        headers = {
            'Authorization': 'Basic OnBhc3N3b3Jk',
            'Content-Type': 'video/webm'
        }
        url = f"https://storage.sia.video.wiki/api/worker/objects/videowiki/{file_name}"

        # Send GET request
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            binary_data = response.content

            return HttpResponse(binary_data, content_type='video/webm')
        else:
            return JsonResponse({'error': 'Failed to download file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Swarm



class StartUploadViewSwarm(APIView):
    def post(self, request, *args, **kwargs):
        video_url = request.data['video_url']

        if not video_url:
            return Response({"error": "video_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        task = download_and_upload.delay(video_url)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)

class TaskStatusViewSwarm(APIView):
    def get(self, request, task_id, *args, **kwargs):
        status_info = check_upload_status(task_id)
        return Response(status_info, status=status.HTTP_200_OK)


#SIA CELERY
class VideoUploadViewSIA(APIView):
    def post(self, request, *args, **kwargs):
        file_url = request.data['file_url']
        task = upload_video_task.delay(file_url)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)

class VideoDownloadViewSIAC(APIView):
    def get(self, request, *args, **kwargs):
        file_name = request.GET.get('file_name')
        task = download_video_task.delay(file_name)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)

class TaskStatusView(APIView):
    def get(self, request, task_id, *args, **kwargs):
        task = app.AsyncResult(task_id)
        if task.state == 'SUCCESS':
            if 'binary_data' in task.result:
                binary_data = base64.b64decode(task.result['binary_data'])
                return HttpResponse(binary_data, content_type='video/webm')
            return JsonResponse(task.result)
        else:
            return JsonResponse({"task_id": task_id, "state": task.state}, status=status.HTTP_200_OK)


class DownloadSwarmFileView(APIView):
    def post(self, request):
        hash = request.data.get('hash')
        if hash:
            result = download_file.delay(hash)
            return Response({'task_id': result.id}, status=status.HTTP_202_ACCEPTED)
        return Response({'error': 'Hash is required'}, status=status.HTTP_400_BAD_REQUEST)

