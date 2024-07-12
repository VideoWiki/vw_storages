from django.urls import path
from swarm.views import FileUploadAPI, FileUploadStatusAPI, FileDownloadAPI, FileDownloadStatusAPI, VideoUploadViewSIA, VideoDownloadViewSIA, StartUploadViewSwarm, TaskStatusViewSwarm, VideoUploadViewSIA, VideoDownloadViewSIAC, TaskStatusView

urlpatterns = [
    path('swarm/upload/', FileUploadAPI.as_view(), name='swarm-file-upload'),
    path('swarm/upload/status/<str:task_id>/', FileUploadStatusAPI.as_view(), name='swarm-file-upload-status'),
    path('swarm/download/', FileDownloadAPI.as_view(), name='swarm-file-download'),
    path('download/status/<str:task_id>/', FileDownloadStatusAPI.as_view(), name='file-download-status'),
    path('sia/upload/', VideoUploadViewSIA.as_view(), name='sia-file-upload'),
    path('sia/download/', VideoDownloadViewSIA.as_view(), name='sia-file-upload'),
    path('swarm-upload/', StartUploadViewSwarm.as_view(), name='swarm-file-upload'),
    path('swarm-status/<str:task_id>/', TaskStatusViewSwarm.as_view(), name='swarm-file-upload-status'),
    path('upload/sia/', VideoUploadViewSIA.as_view(), name='upload_video'),
    path('download/sia/', VideoDownloadViewSIAC.as_view(), name='download_video'),
    path('sia-status/<str:task_id>/', TaskStatusView.as_view(), name='task_status'),
]

