import os
import uuid
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .tasks import upload_file_task, upload_file_url_task
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
from rest_framework.status import HTTP_400_BAD_REQUEST
from dotenv import load_dotenv
from azure.storage.blob import BlobClient
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
load_dotenv()
CONTAINER = os.environ.get('CONTAINER')
CONNECT_STR=os.environ.get('CONNECT_STR')
ROOM_URL = os.environ.get('ROOM_URL')
ROOM_URL2 = os.environ.get('ROOM_URL2')
class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [HasAPIKey]

    def post(self, request, *args, **kwargs):
        file_obj = request.data['file']
        azure_container = request.data['azure_container']
        azure_connect_str = request.data['azure_connect_str']
        if azure_container == "" and azure_connect_str == "":
            container_name = str(CONTAINER)
            connect_str = str(CONNECT_STR)
        else:
            container_name = str(azure_container)
            connect_str = str(azure_connect_str)

        # Create a BlobServiceClient object using the connection string
        connect_str = connect_str
        blob_service_client = BlobServiceClient.from_connection_string(connect_str, connection_timeout=600,
                                                                       read_timeout=600)

        # Create a ContainerClient object for the container
        try:
            container_client = blob_service_client.create_container(container_name)
        except ResourceExistsError:
            container_client = blob_service_client.get_container_client(container_name)

        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        # Start the file upload task asynchronously using Celery
        if hasattr(file_obj, 'file'):
            file_path = os.path.join(settings.MEDIA_ROOT, file_obj.name)
            file_data = file_obj.read()
            # Save the file locally
            with open(file_path, 'wb') as f:
                f.write(file_data)
            upload_file_task.delay(connect_str, container_name, file_obj.name, file_path, task_id)
            # Return the task ID
            return JsonResponse({'task_id': task_id})
        elif file_obj.startswith('http://') or file_obj.startswith('https://'):
            if file_obj.startswith(str(ROOM_URL)) or file_obj.startswith(str(ROOM_URL2)):
                file_name = file_obj.split("/")[-2] + "." + file_obj.split("/")[-1].split(".")[-1]
                file_path = os.path.join(settings.MEDIA_ROOT, file_name)
                upload_file_url_task.delay(connect_str, container_name, file_name, file_path, task_id, file_obj)
                # Return the task ID
                return JsonResponse({'task_id': task_id})
            file_name = f'{uuid.uuid4()}' + file_obj.split('/')[-1]
            file_path = os.path.join(settings.MEDIA_ROOT, file_name + file_obj.split('/')[-1])
            upload_file_url_task.delay(connect_str, container_name, file_name, file_path, task_id, file_obj)
            # Return the task ID
            return JsonResponse({'task_id': task_id})


class FileUploadStatusView(APIView):
    permission_classes = [HasAPIKey]
    def get(self, request, *args, **kwargs):
        task_id = request.GET.get('task_id')

        # Check if the task result is in Redis
        file_url = redis_client.get(task_id)
        if file_url is None:
            # The task result is not in Redis, so the task is still running
            return JsonResponse({'status': 'PENDING'})

        # The task result is in Redis, so the task has completed
        return JsonResponse({'status': 'SUCCESS', 'file_url': file_url.decode('utf-8')})


class AzureBlobDeleteView(APIView):
    permission_classes = [HasAPIKey]
    def post(self, request, *args, **kwargs):
        # Get the URL of the blob to delete from the request data
        blob_url = request.data.get('blob_url')
        azure_connect_str = request.data.get('azure_connect_str')

        # Parse the blob URL to get the container name and blob name
        blob_client = BlobClient.from_blob_url(blob_url)
        container_name = blob_client.container_name
        blob_name = blob_client.blob_name
        # Create a BlobClient for the blob to delete
        if azure_connect_str == "":
            connect_str = str(CONNECT_STR)
        else:
            connect_str = azure_connect_str
        blob_client = BlobClient.from_connection_string(connect_str, container_name=container_name, blob_name=blob_name)

        # Delete the blob
        try:
            blob_client.delete_blob()
        except Exception as e:
            # Return an error response if the blob could not be deleted
            return JsonResponse({'success': False, 'error': str(e)}, status=HTTP_400_BAD_REQUEST)

        # Return a success response if the blob was deleted
        return JsonResponse({'success': True})
