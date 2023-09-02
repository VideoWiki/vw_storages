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
