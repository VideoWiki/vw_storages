from django.urls import path
from swarm.views import FileUploadAPI, FileUploadStatusAPI, FileDownloadAPI, FileDownloadStatusAPI, VideoUploadViewSIA, VideoDownloadViewSIA

urlpatterns = [
    path('swarm/upload/', FileUploadAPI.as_view(), name='swarm-file-upload'),
    path('swarm/upload/status/<str:task_id>/', FileUploadStatusAPI.as_view(), name='swarm-file-upload-status'),
    path('swarm/download/', FileDownloadAPI.as_view(), name='swarm-file-download'),
    path('download/status/<str:task_id>/', FileDownloadStatusAPI.as_view(), name='file-download-status'),
    path('sia/upload/', VideoUploadViewSIA.as_view(), name='sia-file-upload'),
    path('sia/download/', VideoDownloadViewSIA.as_view(), name='sia-file-upload'),

]

