from django.shortcuts import render, render_to_response
from .models import *
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.template import RequestContext
from django.http.response import HttpResponseRedirect, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from Galeria.SpeechDetector import SpeechDetector, GRAMMAR
from Galeria.tasks import *
from threading import Thread
import json


# from .SimpleMFRC522 import SimpleMFRC522

# import RPi.GPIO as GPIO

# Create your views here.


def start_new_thread(f):
    def decorator(*args, **kwargs):
        t = Thread(target=f, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator



decoder = SpeechDetector()

@start_new_thread
def init_decoder(dec):
    dec.__init__()
    dec.set_grammar("grammar", GRAMMAR)
    dec.set_search("grammar")

init_decoder(decoder)


def video_serializer(video, speech):
    keylist = []
    for key in video.keyword.all():
        keylist.append(key.keyword)
    return {'speech': speech, 'type': "video", 'id': video.id_multimedia, 'titulo': video.titulo,
            'src': video.fichero_video.url, 'keywords': keylist}


def image_serializer(image, speech):
    keylist = []
    for key in image.keyword.all():
        keylist.append(key.keyword)
    return {'speech': speech, 'type': "imagen", 'id': image.id_multimedia, 'titulo': image.titulo,
            'src': image.fichero_imagen.url, 'thumbnail': image.thumbnail.url,
            'keywords': keylist}

# TODO: Add decode_speech to celery queue
def decode_speech(audio_file):
    decoder.decode_phrase(audio_file)

    if decoder.get_hyp() == "":
        phrase_recognized = ""
    else:
        phrase_recognized = decoder.get_hyp()

    return phrase_recognized

# def decode_speech(audio_file):
#     decoder.decode_phrase(audio_file)
#
#     # If the keyword "ordenador" is spotted, then switch to jsgf mode
#     # Speech Example: Ordenador show me photos of Sara
#     if decoder.get_hyp() == "ordenador":
#         print ("BINGOOOO")
#         print(decoder.get_search_method())
#         decoder.set_search("grammar")
#         # Grammar search for " show me photos of Sara" which is defined in jsgf file, so phrase_recognized get that value.
#         phrase_recognized = decoder.get_hyp()
#         print (phrase_recognized)
#     else:
#         # If no keyword spotted, switch to kws mode
#         decoder.set_search("keyword")
#         phrase_recognized = ""
#     # if decoder.get_hyp() == "":
#     #     phrase_recognized = ""
#     # else:
#     #     phrase_recognized = decoder.get_hyp()
#     return phrase_recognized


def process_speech(request, recognized_audio):
    keylist = []
    url = ''  # Is the URL where the user will be redirected once speech has been procesed
    if recognized_audio.find("todas") != -1:
        imagenes_filtered = Galeria.models.Imagen.objects.all().filter(album__usuario=request.user)
        return {'type': 0, 'objects': imagenes_filtered}

    if recognized_audio.find("todos los videos") != -1:
        videos_filtered = Galeria.models.Video.objects.all().filter(album__usuario=request.user)
        return {'type': 1, 'objects': videos_filtered}

    if recognized_audio.find('ver fotos') != -1 \
            or recognized_audio.find('mostrar fotos') != -1 \
            or recognized_audio.find('ver imágenes') != -1 \
            or recognized_audio.find('mostrar imágenes') != -1 \
            or recognized_audio.find('ver fotografías') != -1 \
            or recognized_audio.find('mostrar fotografías') != -1:

        # for word in recognized_audio.split(" "):
        #     if word in Galeria.models.Keyword.objects.all():
        #         keylist.append(word)
        for key in Galeria.models.Keyword.objects.all():
            if recognized_audio.find(key.keyword.lower()) != -1:
                keylist.append(key)
        print('Identificado Keyword: ', keylist)
        albums = Galeria.models.Album.objects.filter(keywords__in=keylist, usuario__exact=request.user)
        if albums:
            imagenes_filtered = Galeria.models.Imagen.objects.filter(album__in=albums)
        else:
            imagenes_filtered = Galeria.models.Imagen.objects.filter(keyword__keyword__in=keylist,
                                                                 album__usuario=request.user).distinct()
        # print(imagenes_filtered)
        return {'type': 0, 'objects': imagenes_filtered}
    if recognized_audio.find('ver videos') != -1\
            or recognized_audio.find('mostrar videos') != -1:
        for key in Galeria.models.Keyword.objects.all():
            if recognized_audio.find(key.keyword.lower()) != -1:
                keylist.append(key)
        print('Identificado Keyword: ', keylist)
        print("Reconocido VIDEO")
        videos_filtered = Galeria.models.Video.objects.filter(keyword__keyword__in=keylist,
                                                              album__usuario=request.user).distinct()
        return {'type': 1, 'objects': videos_filtered}
    if (recognized_audio.find('ver') != -1
            or recognized_audio.find('mostrar') != -1):
        print("Reconocido VER")
        return "ver"
    if (recognized_audio.find('siguiente') != -1
            or recognized_audio.find('adelante') != -1):
        print("Reconocido SIGUIENTE")
        return "siguiente"
    if (recognized_audio.find('anterior') != -1
            or recognized_audio.find('atrás') != -1):
        print("Reconocido ANTERIOR")
        return "anterior"
    if (recognized_audio.find('salir') != -1
            or recognized_audio.find('cerrar') != -1):
        print("Reconocido SALIR")
        return "salir"
    if recognized_audio.find('subir volumen') != -1:
        print("Reconocido VolumeUP")
        return "volumeUp"
    if recognized_audio.find('bajar volumen') != -1:
        print("Reconocido VolumeDown")
        return "volumeDown"
    if recognized_audio.find('pausa') != -1 \
            or recognized_audio.find('parar') != -1:
        print("Reconocido pausa")
        return "pausa"
    if recognized_audio.find('reproducir') != -1 \
            or recognized_audio.find('continuar') != -1:
        print("Reconocido play")
        return "play"
    if recognized_audio.find('menu principal') != -1 \
            or recognized_audio.find('menu') != -1:
        print("Reconocido Menú Principal")
        return "menu"
    if recognized_audio == 'fotos'\
            or recognized_audio == 'fotografías'\
            or recognized_audio == 'pivoz imágenes':
        print("Reconocido Menú-Fotos")
        return "menu-fotos"
    if recognized_audio.find('videos') != -1:
        print("Reconocido Menú-Videos")
        return "menu-videos"
    if recognized_audio.find('album') != -1:
        print("Reconocido Menú-Álbum")
        return "menu-album"
    if recognized_audio.find('radio') != -1:
        print("Reconocido Menú-Radios")
        return "menu-radio"




@login_required
def upload(request):
    print("Método: ", request.method)
    print("Ajax: ", request.is_ajax())
    if request.method == 'POST':
        if request.FILES.get('audio'):
            record_audio = request.FILES['audio']
            print("Audio name: ", record_audio.name)
            fs = FileSystemStorage()
            filename = fs.save(record_audio.name + ".wav", record_audio)
            speech = decode_speech(filename)
            #speech = speech.get(timeout=1)
            # run = decode_speech.delay(filename)
            # speech = decode_speech.AsyncResult(run.id)
            # speech = speech.get()
            # Eliminamos el audio que ya ha sido procesado
            audio = record_audio.name + '.wav'
            fs.delete(audio)
            if speech == "":
                return JsonResponse({'error': 'No se ha reconocido nada. Pruebe a decir: ver todas las fotos'})
            else:
                # speech = "Ver fotos de caballos"
                print(speech)
                if process_speech(request, speech) == "ver":
                    return JsonResponse({'comando': 'ver', 'speech': speech})
                if process_speech(request, speech) == "siguiente":
                    return JsonResponse({'comando': 'siguiente', 'speech': speech})
                if process_speech(request, speech) == "anterior":
                    return JsonResponse({'comando': 'anterior', 'speech': speech})
                if process_speech(request, speech) == "salir":
                    return JsonResponse({'comando': 'salir', 'speech': speech})
                if process_speech(request, speech) == "volumeUp":
                    return JsonResponse({'comando': 'volumeUp', 'speech': speech})
                if process_speech(request, speech) == "volumeDown":
                    return JsonResponse({'comando': 'volumeDown', 'speech': speech})
                if process_speech(request, speech) == "pausa":
                    return JsonResponse({'comando': 'pausa', 'speech': speech})
                if process_speech(request, speech) == "play":
                    return JsonResponse({'comando': 'play', 'speech': speech})
                if process_speech(request, speech) == "menu":
                    return JsonResponse({'comando': 'menu', 'speech': speech})
                if process_speech(request, speech) == "menu-fotos":
                    return JsonResponse({'comando': 'menu-fotos', 'speech': speech})
                if process_speech(request, speech) == "menu-album":
                    return JsonResponse({'comando': 'menu-albums', 'speech': speech})
                if process_speech(request, speech) == "menu-videos":
                    return JsonResponse({'comando': 'menu-videos', 'speech': speech})
                if process_speech(request, speech) == "menu-radio":
                    return JsonResponse({'comando': 'menu-radios', 'speech': speech})
                objects = process_speech(request, speech)['objects']  # Guardo los e. multimedia obtenidos
                contentType = process_speech(request, speech)['type']  # Type 0: Imagenes // Type 1: Videos
                # data = serializers.serialize('json', objects, fields=('titulo', 'fichero_imagen'))
                if contentType == 0:
                    imagenes = [image_serializer(imagen, speech) for imagen in objects]
                    return HttpResponse(json.dumps(imagenes), content_type='application/json')
                if contentType == 1:
                    videos = [video_serializer(video, speech) for video in objects]
                    return HttpResponse(json.dumps(videos), content_type='application/json')
        else:
            return render_to_response('index.html', {"error": "No se ha podido grabar audio. Contacte con administrador."}, RequestContext(request))
    else:
        return HttpResponseRedirect('/home/')


@login_required()
def imageGallery(request):
    imagenes = Imagen.objects.all().filter(album__usuario=request.user)
    return render_to_response('fotos.html', locals(), RequestContext(request))


@login_required()
def videoGallery(request):
    videos = Video.objects.all().filter(album__usuario=request.user)
    return render_to_response('videoGallery.html', locals(), RequestContext(request))


@login_required()
def musicGallery(request):
    return render_to_response("musica.html", locals(), RequestContext(request))


# @login_required()
# def albumGallery(request):
#     return render_to_response("album.html")


def radio(request):
    radios = Radio.objects.all()
    return render_to_response("radios.html", locals(), RequestContext(request))


def musica(request):
    musica = Musica.objects.all()
    return render_to_response("playlist.html", locals(), RequestContext(request))


def playlist(request):
    return render_to_response('playlist.html', context=None)


def thanks(request):
    return render_to_response('thanks.html', RequestContext(request))


def userView(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = Usuario

    return render_to_response('index.html', locals())


def record_web_audio(request):
    uploaded_file = open("recording.ogg", "wb")
    uploaded_file.write(request.body)
    uploaded_file.close()

    return render_to_response("index.html", locals())


def albumGallery(request):
    list = Album.objects.filter(usuario=request.user)

    return render(request, 'albums.html', {'albums': list})


def AlbumDetail(request, slug):
    imagenes = Imagen.objects.all().filter(album__slug__iexact=slug)
    print(slug)
    return render_to_response('fotos.html', locals(), RequestContext(request))

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@staff_member_required
def read_rfid(request, user):
        if request.method == 'POST':
            usuario = request.POST.get("usuario")
            rfid_id = request.POST.get("rfid_id")
            print(rfid_id)
            print("Usuario: {0} con rfid {1} sera actualizado".format(usuario, rfid_id))
            for user in RegularUser.objects.all():
                if user.rfid == rfid_id:
                    messages.error(request, 'El código rfid {0} ya está asociado a un usuario.'.format(rfid_id))
                    return HttpResponseRedirect(reverse('admin:galeria_imagen_changelist'))
            if usuario is not None and rfid_id != "":
                RegularUser.objects.filter(pk=usuario).update(rfid=rfid_id)
                messages.success(request, 'El código RFID {0} se ha asociado al usuario {1} con éxito'.format(rfid_id, usuario.username))
                return HttpResponseRedirect(reverse('admin:index'))
        else:
            client_ip = get_client_ip(request)
            print (client_ip)
            return render_to_response('read_rfid.html', {'user': user, 'cliente': client_ip})

def delete_rfid(request, user):
    usuario = RegularUser.objects.get(pk=user)
    RegularUser.objects.filter(pk=user).update(rfid="")
    messages.success(request, 'Usuario {0} modificado con éxito'.format(usuario.username))
    return HttpResponseRedirect(reverse('admin:Galeria_regularuser_change', args=(user,)))
