from django.shortcuts import render, render_to_response, get_object_or_404
from .models import *
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.template import RequestContext
from django.http.response import HttpResponseRedirect, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.utils.timezone import utc
from .forms import ShareUserForm
from django.http import JsonResponse
from django.db.models.signals import post_save
from django.dispatch import receiver
from Galeria.SpeechDetector import SpeechDetector, GRAMMAR
from Galeria.tasks import *
from threading import Thread
import json
import datetime


# Create your views here.




# Creamos una instancia SpeechDetector()
decoder = SpeechDetector()



# Inicializamos el decodificador. El decodificador es una instancia de la clase SpeechDetector() y será el encargado de
# reconocer los comandos de voz

def init_decoder():
    decoder.__init__()
    decoder.set_grammar("grammar", GRAMMAR)
    decoder.set_search("grammar")

init_decoder()

# Señal de Django que se ejecuta después de guardar una palabra clave. Reinicializa la configuración del decodificador
# para que cargue el nuevo fichero de gramática.
@receiver(post_save, sender=Keyword)
def update_grammar(sender, **kwargs):
    decoder.set_grammar("grammar", GRAMMAR)

# Señal de Django que se ejecuta después de guardar una instancia de Album. Reinicializa la configuración del decodificador
# para que cargue el nuevo fichero de gramática.
@receiver(post_save, sender=Album)
def update_grammar(sender, **kwargs):
    decoder.set_grammar("grammar", GRAMMAR)


def video_serializer(video, speech):
    """ Función para serializar videos. Permite crear un objeto JSON con los objetos Video

            Parameters
            ----------
                video: Video Object
                    video para serializar
                speech: string
                    comando de voz reconocido

            Returns
             ------
                dict
                    Diccionario JSON serializado

    """
    keylist = []
    for key in video.keyword.all():
        keylist.append(key.keyword)
    return {'speech': speech, 'type': "video", 'id': video.id, 'titulo': video.titulo,
            'src': video.fichero_video.url, 'keywords': keylist}


def image_serializer(image, speech):
    """ Función para serializar imágenes. Permite crear un objeto JSON con los objetos Imagen

                Parameters
                ----------
                    image: Image Object
                        imagen para serializar
                    speech: string
                        comando de voz reconocido

                Returns
                 ------
                    dict
                        Diccionario JSON serializado

        """
    keylist = []
    for key in image.keyword.all():
        keylist.append(key.keyword)
    return {'speech': speech, 'type': "imagen", 'id': image.id, 'titulo': image.titulo,
            'src': image.fichero_imagen.url, 'thumbnail': image.thumbnail.url,
            'keywords': keylist}


def radio_serializer(radio, speech):
    """ Función para serializar radios. Permite crear un objeto JSON con los objetos Radio

                Parameters
                ----------
                    radio: Radio Object
                        radio para serializar
                    speech: string
                        comando de voz reconocido

                Returns
                 ------
                    dict
                        Diccionario JSON serializado

        """
    return {'speech': speech, 'type': "radio", 'id': radio.id, 'titulo': radio.nombre,
            'src': radio.url}


# TODO: Add decode_speech to celery queue
def decode_speech(audio_file):
    """ Permite decodificar un fichero de audio y transcribirlo a texto

                Parameters
                ----------
                    audio_file: FileSystemStorage
                        archivo de audio con el comando de voz


                Returns
                 ------
                    string
                        Comando reconocido

        """
    decoder.decode_phrase(audio_file)

    if decoder.get_hyp() == "":
        phrase_recognized = ""
    else:
        phrase_recognized = decoder.get_hyp()
        print(phrase_recognized)

    return phrase_recognized


def process_speech(request, recognized_audio):
    """ Función para procesar el comando de voz

                Parameters
                ----------
                    request: HTTPRequest Object
                        petición del usuario
                    recognized_audio: string
                        comando de voz reconocido

                Returns
                 ------
                    dict
                        Diccionario de objetos
                    string
                        comando

        """
    keylist = []
    if recognized_audio.find("todas las fotos") != -1:
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

        for key in Galeria.models.Keyword.objects.all():
            if recognized_audio.find(key.keyword.lower()) != -1:
                keylist.append(key)

        albums = Galeria.models.Album.objects.filter(keywords__in=keylist, usuario__exact=request.user)
        if albums:
            imagenes_filtered = Galeria.models.Imagen.objects.filter(album__in=albums)
        elif recognized_audio.find(" en ") != -1:
            ubicacion = recognized_audio.split(" en ")[1]
            album = Album.objects.filter(address__icontains=ubicacion)
            if len(keylist) > 0:
                imagenes_filtered = Galeria.models.Imagen.objects.filter(keyword__keyword__in=keylist,
                                                                         album__in=album,
                                                                         album__usuario=request.user).distinct()
            else:
                imagenes_filtered = Galeria.models.Imagen.objects.filter(album__in=album,
                                                                         album__usuario=request.user).distinct()
        else:
            imagenes_filtered = Imagen.objects.filter(keyword__keyword__in=keylist,
                                                      album__usuario=request.user).distinct()

        return {'type': 0, 'objects': imagenes_filtered}
    if recognized_audio.find('ver videos') != -1 \
            or recognized_audio.find('mostrar videos') != -1:
        for key in Galeria.models.Keyword.objects.all():
            if recognized_audio.find(key.keyword.lower()) != -1:
                keylist.append(key)
        print('Identificado Keyword: ', keylist)
        videos_filtered = Galeria.models.Video.objects.filter(keyword__keyword__in=keylist,
                                                              album__usuario=request.user).distinct()
        return {'type': 1, 'objects': videos_filtered}
    if (recognized_audio == "pivoz ver"
            or recognized_audio == "pivoz mostrar"):
        return "ver"
    if (recognized_audio == "pivoz siguiente"
            or recognized_audio == "pivoz adelante"):
        return "siguiente"
    if (recognized_audio == "pivoz anterior"
            or recognized_audio == "pivoz atrás"):
        return "anterior"
    if (recognized_audio == "pivoz salir"
            or recognized_audio == "pivoz cerrar"):
        return "salir"
    if recognized_audio == "pivoz subir volumen":
        return "volumeUp"
    if recognized_audio == "pivoz bajar volumen":
        return "volumeDown"
    if recognized_audio == "pivoz pausa" \
            or recognized_audio == "pivoz parar":
        return "pausa"
    if recognized_audio == "pivoz reproducir" \
            or recognized_audio == "pivoz continuar":
        return "play"
    if recognized_audio == "pivoz menu principal" \
            or recognized_audio == "pivoz menu":
        return "menu"
    if recognized_audio == "pivoz fotos" \
            or recognized_audio == "pivoz fotografías" \
            or recognized_audio == "pivoz imágenes":
        return "menu-fotos"
    if recognized_audio == "pivoz videos":
        return "menu-videos"
    if recognized_audio == "pivoz album" \
            or recognized_audio == "pivoz albumes":
        return "menu-album"
    if recognized_audio == "pivoz radio":
        return "menu-radio"
    if recognized_audio == "pivoz mi perfil":
        return "profile"
    if recognized_audio.startswith("pivoz pon"):
        for key in Galeria.models.Keyword.objects.all():
            if recognized_audio.find(key.keyword.lower()) != -1:
                keylist.append(key)
        radios_filtered = Radio.objects.get(keyword__keyword__in=keylist)
        return {'type': 2, 'objects': radios_filtered}


@login_required
def upload(request):
    """ Vista para subir el fichero de audio y responder la petición AJAX. En esta parte respondemos la petición AJAX
    con el comando reconocido o bien con los objetos filtrados, ya sean Imágenes, Videos o Radios.

                Parameters
                ----------
                    request: HTTPRequest

                Returns
                 ------
                    JsonResponse
                        Diccionario de objetos en formato JSON

        """
    print("Método: ", request.method)
    print("Ajax: ", request.is_ajax())
    if request.method == 'POST':
        if request.FILES.get('audio'):
            record_audio = request.FILES['audio']
            print("Audio name: ", record_audio.name)
            fs = FileSystemStorage()
            filename = fs.save(record_audio.name + ".wav", record_audio)
            speech = decode_speech(filename)
            # Eliminamos el audio que ya ha sido procesado
            audio = record_audio.name + '.wav'
            fs.delete(audio)
            if speech == "":
                return JsonResponse({'error': 'No se ha reconocido nada. Pruebe a decir: ver todas las fotos'})
            else:
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
                if process_speech(request, speech) == "profile":
                    return JsonResponse({'comando': 'profile', 'speech': speech})
                if (process_speech(request, speech)['objects']):
                    objects = process_speech(request, speech)['objects']  # Guardo los e. multimedia obtenidos
                    contentType = process_speech(request, speech)['type']  # Type 0: Imagenes // Type 1: Videos // Type 2: Radio
                    if contentType == 0:
                        imagenes = [image_serializer(imagen, speech) for imagen in objects]
                        return HttpResponse(json.dumps(imagenes), content_type='application/json')
                    if contentType == 1:
                        videos = [video_serializer(video, speech) for video in objects]
                        return HttpResponse(json.dumps(videos), content_type='application/json')
                    if contentType == 2:
                        radios = radio_serializer(objects, speech)
                        return HttpResponse(json.dumps(radios), content_type='application/json')
        else:
            return render_to_response('index.html',
                                      {"error": "No se ha podido grabar audio. Contacte con administrador."},
                                      RequestContext(request))
    else:
        return HttpResponseRedirect('/home/')


@login_required()
def image_gallery(request):
    """Vista para mostrar las imágenes del usuario"""
    cliente = get_client_ip(request)
    imagenes = Imagen.objects.all().filter(album__usuario=request.user)
    return render_to_response('fotos.html', locals(), RequestContext(request))


@login_required()
def video_gallery(request):
    """Vista para mostrar los videos del usuario"""
    videos = Video.objects.all().filter(album__usuario=request.user)
    return render_to_response('videoGallery.html', locals(), RequestContext(request))


@login_required()
def music_gallery(request):
    """Vista para mostrar el menú de música"""
    return render_to_response("musica.html", locals(), RequestContext(request))


def album_gallery(request):
    """Vista para mostrar los álbumes del usuario"""
    list = Album.objects.filter(usuario=request.user)
    return render(request, 'albums.html', {'albums': list})


def radio(request):
    """Vista para mostrar las emisoras de radio del usuario"""
    radios = Radio.objects.all()
    return render_to_response("howler_radio.html", locals(), RequestContext(request))


def album_detail(request, slug):
    """Vista para mostrar el contenido de un álbum del usuario"""
    imagenes = Imagen.objects.all().filter(album__slug__iexact=slug)
    videos = Video.objects.filter(album__slug__iexact=slug)
    slug = slug.replace('-', ' ')
    return render_to_response('fotos.html', locals(), RequestContext(request))


def get_client_ip(request):
    """Devuelve la dirección IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def read_rfid(request, user):
    """ Vista utilizada para asociar un codigo RFID al usuario

                Parameters
                ----------
                    request: HTTPRequest
                    user: RegularUser Object

                Returns
                 ------
                    HttpResponseRedirect
                        redirección a la página especificada

        """
    usuario = RegularUser.objects.get(pk=user)
    list = []
    for u in RegularUser.objects.all():
        if u.rfid != "":
            list.append(u.rfid)
    for entry in RFIDMiddleware.objects.all():
        if (datetime.datetime.utcnow().replace(tzinfo=utc) - entry.timestamp).total_seconds() < 20:
            if entry.rfid_id in list:
                messages.error(request,
                               'El código RFID {0} ya está en uso. Por favor, inténtelo de nuevo con otro código.'.format(
                                   entry.rfid_id))
                return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))
            RegularUser.objects.filter(pk=user).update(rfid=entry.rfid_id)
            entry.delete()
            messages.success(request, 'El código RFID {0} se ha asociado al usuario {1} con éxito'.format(entry.rfid_id,
                                                                                                          usuario.username))
            return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))
    messages.error(request,
                   'Por favor, acerca el nuevo código RFID al lector para asociarlo a {0} y vuelva a pulsar Vincular pulsera'.format(
                       usuario.username))
    return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))





@staff_member_required
def delete_rfid(request, user):
    """ Elimiar código RFID del usuario

                    Parameters
                    ----------
                        request: HTTPRequest
                        user: RegularUser Object
                            usuario que va a ser actualizado

                    Returns
                     ------
                        HttpResponseRedirect
                            redirección a la página especificada

            """

    usuario = get_object_or_404(RegularUser, pk=user)
    if usuario.rfid != "":
        RegularUser.objects.filter(pk=user).update(rfid="")
        messages.success(request, 'Usuario {0} modificado con éxito'.format(usuario.username))
    else:
        messages.warning(request, 'El usuario {0} no tiene ningún código RFID asociado.'.format(usuario.username))
    return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))

@staff_member_required
def share_user(request, user):
    """ Permite al administrador compartir un usuario

                    Parameters
                    ----------
                        request: HTTPRequest
                        user: RegularUser Object
                            usuario que va a ser actualizado
                    Returns
                     ------
                        HttpResponseRedirect
                            redirección a la página especificada

            """
    if request.method == 'POST':
        form = ShareUserForm(request.POST)
        if form.is_valid():
            admin = form.cleaned_data["administrador"]
            try:
                administrador = AdminUser.objects.get(username=admin)
                try:
                    usuario = RegularUser.objects.get(pk=user)
                except RegularUser.DoesNotExist:
                    messages.error(request, "El usuario {0} no existe.".format(usuario.username))
                    return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))
            except AdminUser.DoesNotExist:
                messages.error(request, "El administrador {0} no existe.".format(admin))
                return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))
            usuario.adminuser_set.add(administrador)
            messages.success(request, "Ahora {0} es un administrador de {1}".format(admin, usuario.username))
            return HttpResponseRedirect(reverse('admin:Galeria_regularuser_changelist'))
    else:
        form = ShareUserForm()
        return render(request, 'admin/share_user.html', {'user': user, 'form': form})
