"""untitled URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-basbaseded views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, re_path
from .views import imageGallery, videoGallery, musicGallery, radio, playlist, record_web_audio, upload, AlbumDetail, \
    albumGallery, read_rfid, delete_rfid

#app_name = 'galeria'
urlpatterns = [
    path('images/', imageGallery, name="imageGallery"),
    path('videos/', videoGallery, name="videoGallery"),
    path('music/', musicGallery, name="musicGallery"),
    path('albums/', albumGallery, name="albumsGallery"),
    path('playlist/', playlist, name="playlist"),
    path('music/radio', radio, name="radios"),
    path('recorder/', record_web_audio, name="recorder"),
    path('uploadAudio/', upload, name="uploadAudio"),
    path('albumImage/<slug:slug>/', AlbumDetail, name="albumsGalleryDetailView"),
    re_path(r'^RFID/(?P<user>\d+)/$', read_rfid, name="ReadRFID"),
    re_path(r'^deleteRFID/(?P<user>\d+)/$', delete_rfid, name="deleteRFID"),


]
