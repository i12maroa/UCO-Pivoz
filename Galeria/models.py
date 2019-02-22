from django.db import models
from django.contrib.auth.models import AbstractUser, User
from phonenumber_field.modelfields import PhoneNumberField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.utils.safestring import mark_safe
import os
from django.utils.text import slugify
from .validators import validate_file_extension, validate_keyword, alphabetic
from Galeria.tasks import check_dictionary, add_keyword_to_dict, update_grammar
from django.core.validators import RegexValidator
from django_google_maps import fields as map_fields
from time import gmtime, strftime

from PiVoz.settings import BASE_DIR
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import django_filters

# Create your models here.

GENERO_CHOICES = (
    ("POP", "Pop"),
    ("ROCK", "Rock"),
    ("ELECTRONICA", "Electrónica"),
    ("RAP", "Rap"),
    ("REGGAE", "Reggae"),
    ("LATINA", "Latina"),
    ("CLASICA", "Clásica"),
    ("BACHATA", "Bachata"),
    ("METAL", "Metal"),
    ("BSO", "Banda Sonora"),
    ("SALSA", "Salsa"),
    ("PUNK", "Punk"),
    ("JAZZ", "Jazz"),
    ("FLAMENCO", "Flamenco / Sevillanas"),
    ("DANCE", "Dance"),
    ("HOUSE", "House"),
    ("DISCO", "Disco"),
    ("COUNTRY", "Country"),
    ("BLUES", "Blues"),
    ("OPERA", "Opera"),
    ("TANGO", "Tango"),
    ("SOUL", "Soul"),
    ("MERENGUE", "Merengue"),
    ("BOLERO", "Bolero"),
    ("FOLK", "Folk"),
    ("ALTERNATIVA", "Alternativa"),
    ("OTRO", "Otro"),
)


def get_upload_path(instance, filename):
    """Función para obtener el directorio donde se almacenarán los archivos multimedia
    de cada usuario. Dependerá del tipo de fichero que guarde"""

    # Thumbnails de Albums
    if isinstance(instance, Album):
        return 'users/{0}/albums/{1}/portada/{2}'.format(instance.created_by, instance.titulo, filename)
    # Imagenes. En este caso se almacenará en la carpeta del álbum al que corresponda
    if isinstance(instance, Imagen):
        album = instance.get_album_title()
        created_by = instance.get_admin_name()
        return 'users/{0}/albums/{1}/fotos/{2}'.format(created_by, album, filename)
    # Videos. Igual que el caso anterior pero en videos
    if isinstance(instance, Video):
        album = instance.get_album_title()
        created_by = instance.get_admin_name()
        return 'users/{0}/albums/{1}/videos/{2}'.format(created_by, album, filename)
    # Imagenes de perfil: Por defecto se almacenarán en una carpeta predefinida en el sistema: /img/avatars



class MyUser(AbstractUser):
    descripcion = models.TextField(blank=True, verbose_name="Sobre ti", help_text="Añade algo de información sobre ti.")
    telefono = PhoneNumberField()
    avatar = models.ImageField(verbose_name='Imagen de perfil',
                               upload_to='img/avatars',
                               default='img/avatars/avatar-placeholder-generic.png')

    def __str(self):
        return self.username

class RegularUser(MyUser):
    rfid = models.CharField(max_length=12, validators=[RegexValidator(r'^\d{1,10}$')],
                            help_text="Selecciona la opción \"Vincular Pulsera\" en el panel de acciones para establecer un RFID.",
                            verbose_name="RFID", blank=True)
    MyUser.is_staff = False
    MyUser.is_superuser = False

    class Meta:
        verbose_name = 'Usuario Regular'
        verbose_name_plural = 'Usuarios Regulares'

    def get_admin_user(self):
        admins = AdminUser.objects.filter(usuarios=self)
        return admins


class AdminUser(MyUser):
    usuarios = models.ManyToManyField(RegularUser, help_text="Selecciona los usuarios que administra", blank=True)

    class Meta:
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    @classmethod
    def create(cls):
        adminUser = cls(is_staff=True)
        adminUser.save()
        return adminUser




# class Evento(models.Model):
#     id_evento = models.AutoField(primary_key=True)
#     nombre = models.CharField(max_length=80, unique=True)
#     ubicacion = models.CharField(max_length=80)
#     fecha_evento = models.DateTimeField()
#
#     class Meta:
#         verbose_name_plural = "Eventos"
#
#     def __str__(self):
#         return self.nombre


class Keyword(models.Model):
    id_keyword = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=20, unique=True, validators=[validate_keyword, alphabetic])
    usuario = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.keyword


class Album(models.Model):
    image_height = models.PositiveSmallIntegerField(default=400)
    image_width = models.PositiveSmallIntegerField(default=400)
    id_album = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=40, null=False)
    descripcion = models.TextField(verbose_name='Descripción del Álbum', blank=True)
    thumbnail = models.ImageField(upload_to=get_upload_path, height_field='image_height', width_field='image_width')
    address = map_fields.AddressField(max_length=200, verbose_name='Ubicación', blank=True,
                                      help_text="Añade información de la ubicación para localizar "
                                                "tomas basándote en el sitio donde fueron tomadas. ¿Asombroso verdad?")
    geolocation = map_fields.GeoLocationField(max_length=100, verbose_name="Geolocaclización", blank=True)
    fecha_creacion = models.DateTimeField(verbose_name='Fecha de creación', auto_now_add=True)
    fecha_modificacion = models.DateTimeField(verbose_name='Última edición', auto_now=True)
    usuario = models.ManyToManyField(RegularUser, related_name="usuario", blank=True)
    created_by = models.ForeignKey(AdminUser, on_delete=models.CASCADE, related_name='Administrador', default=1)
    slug = models.SlugField(max_length=50, unique=True)
    keywords = models.ManyToManyField(Keyword, verbose_name='Evento', blank=True,
                                 help_text="Introduce un evento relacionado con el álbum. Por ejemplo: "
                                           "\"Comunión de mi nieto paco\". Posteriormente, el usuario "
                                           "podrá buscar todas las fotos de un ábum pronunciando el nombre del evento.")

    class Meta:
        verbose_name_plural = "Álbumes"

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        self.slug = slugify(self.titulo)
        super(Album, self).save(*args, **kwargs)

    def thumbnail_tag(self):
        if (self.thumbnail):
            return mark_safe('<img src="/media/%s" width="150" height="150" />' % (self.thumbnail))

    thumbnail_tag.short_description = 'Portada'
    thumbnail_tag.allow_tags = True


class Multimedia(models.Model):
    id_multimedia = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=80, unique=True, default='imagen_{0}'.format(strftime("%Y_%m_%d_%H%M%S")))
    descripcion = models.TextField(blank=True, help_text='Descríbeme...')
    path = models.FilePathField(path='media', allow_folders=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    keyword = models.ManyToManyField('Keyword', help_text="Selecciona las palabras clave para etiquetar.")


    def __str__(self):
        return self.titulo

    def get_admin_name(self):
        return self.album.created_by

    def get_album_title(self):
        return self.album.titulo


class Imagen(Multimedia):
    # titulo = models.CharField(max_length=100)
    image_width = models.PositiveSmallIntegerField(default=640)
    image_height = models.PositiveSmallIntegerField(default=480)
    fichero_imagen = models.ImageField(verbose_name='Archivo de imagen',
                                       upload_to=get_upload_path,
                                       width_field='image_width',
                                       height_field='image_height')
    thumbnail = ImageSpecField(source='fichero_imagen',
                               processors=[ResizeToFill(600, 300)],
                               format='JPEG',
                               options={'quality': 60})


    class Meta:
        verbose_name_plural = "Imágenes"

    def filename(self):
        return os.path.basename(self.fichero_imagen.name)

    def image_tag(self):
        if (self.fichero_imagen):
            return mark_safe('<img src="/media/%s" width="150" height="150" />' % (self.fichero_imagen))

    image_tag.short_description = 'Imagen'
    image_tag.allow_tags = True





class Video(Multimedia):
    fichero_video = models.FileField(verbose_name="Archivo de Vídeo",
                                     upload_to=get_upload_path,
                                     validators=[validate_file_extension])

    class Meta:
        verbose_name_plural = "Videos"


class Musica(Multimedia):
    artista = models.CharField(max_length=150)
    nombre_album = models.CharField(max_length=150)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, default='OTRO')
    music_file = models.FileField(verbose_name="Fichero de Audio", upload_to='files/audio')

    class Meta:
        verbose_name_plural = "Música"
        verbose_name = "Música"


class Radio(models.Model):
    nombre = models.CharField(verbose_name="Nombre", max_length=100, blank=False)
    url = models.URLField(verbose_name="URL de la Radio")
    thumbnail = models.ImageField(verbose_name="Carátula de la Radio",
                                  upload_to='thumbs/radios')
    keyword = models.ManyToManyField('Keyword', help_text="Selecciona las palabras clave para etiquetar.")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Emisoras de radio"
        verbose_name_plural = verbose_name
