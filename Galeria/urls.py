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
from .views import image_gallery, video_gallery, music_gallery, radio, upload, album_detail, \
    album_gallery, read_rfid, delete_rfid, share_user

app_name = 'galeria'
urlpatterns = [
    # Galería de imágenes
    path('images/', image_gallery, name="imageGallery"),
    # Galería de videos
    path('videos/', video_gallery, name="videoGallery"),
    # Musica
    path('music/', music_gallery, name="musicGallery"),
    # Galeria de álbumes
    path('albums/', album_gallery, name="albumsGallery"),
    # Radios
    path('music/radio', radio, name="radios"),
    # Procesar audio de voz
    path('uploadAudio/', upload, name="uploadAudio"),
    # Contenido de álbumes
    path('albumImage/<slug:slug>/', album_detail, name="albumsGalleryDetailView"),
    # Leer RFID
    re_path(r'^RFID/(?P<user>\d+)/$', read_rfid, name="ReadRFID"),
    # Borrar código RFID
    re_path(r'^deleteRFID/(?P<user>\d+)/$', delete_rfid, name="deleteRFID"),
    # Compartir Usuario
    re_path(r'^user/share/(?P<user>\d+)/$', share_user, name="shareUser"),

]
