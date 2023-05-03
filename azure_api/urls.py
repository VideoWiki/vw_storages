from django.urls import path
from .views import FileUploadView, FileUploadStatusView, AzureBlobDeleteView
urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('upload/status/', FileUploadStatusView.as_view(), name='file-upload-status'),
    path('delete-blob/', AzureBlobDeleteView.as_view(), name='file-delete-status'),
]