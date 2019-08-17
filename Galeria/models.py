from django.db import models
from django.contrib.auth.models import AbstractUser, User
from phonenumber_field.modelfields import PhoneNumberField
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFill, Adjust
from imagekit import ImageSpec
from django.utils.safestring import mark_safe
import os
from io import BytesIO
import PIL.ExifTags
from PIL import Image as PILImage
from django.core.files import File
from django.utils.text import slugify
from .validators import validate_file_extension, validate_keyword, alphabetic
from django.core.validators import RegexValidator
from django_google_maps import fields as map_fields
import dateutil.parser
from django.dispatch import receiver
from django.db.models.signals import post_save
from Galeria.tasks import check_dictionary,add_keyword_to_dict, update_grammar
from datetime import datetime


# -------------------------   Funciones utilizadas por los modelos   ------------------------ #



def get_upload_path(instance, filename):

    """ Función para obtener el directorio donde se almacenarán los archivos multimedia
    de cada usuario. Dependerá del tipo de fichero que guarde

                    Parameters
                    ----------
                    instance: object
                        Objeto que va a ser guardado
                    filename
                        nombre del archivo

                    Returns
                    ------
                    string
                        Path donde va a ser almacenado el fichero en el sistema de archivos

            """

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



def compress(image):
    """ Función para comprimir imágenes

                        Parameters
                        ----------
                        image: ImageField
                            Imagen que va a ser comprimida


                        Returns
                        ------
                        FileField
                            imagen comprimida

                """
    im = PILImage.open(image)
    im_io = BytesIO()
    im.save(im_io, 'JPEG', quality=70)
    print ("***************************************** COMPRESSING IMAGE *****************************************")
    new_image = File(im_io, name=image.name)
    return new_image


class MyUser(AbstractUser):
    """Clase utilizada para almacenar la información general de Usuarios administradores y usuarios regulrares"""
    descripcion = models.TextField(blank=True, verbose_name="Sobre ti", help_text="Añade algo de información sobre ti.")
    telefono = PhoneNumberField(blank=True, null=True)
    avatar = models.ImageField(verbose_name='Imagen de perfil',
                               upload_to='img/avatars',
                               default='img/avatars/generic_placeholder.png')
    avatar_thumbnail = ImageSpecField(source='avatar',
                                      processors=[ResizeToFill(100, 80)],
                                      format='JPEG',
                                      options={'quality': 60})

    def __str(self):
        return self.username


class RegularUser(MyUser):
    """Representa los usuarios regulares de la aplicación"""
    rfid = models.CharField(max_length=12, validators=[RegexValidator(r'^\d{1,10}$')],
                            help_text="Selecciona la opción \"Vincular Pulsera\" en el panel de acciones "
                                      "para establecer un RFID.",
                            verbose_name="RFID", blank=True)
    MyUser.is_staff = False
    MyUser.is_superuser = False

    class Meta:
        verbose_name = 'Usuario Regular'
        verbose_name_plural = 'Usuarios Regulares'

    def get_admin_user(self):
        """ Función para obtener los administradores del usuario

                Parameters
                ----------
                self: MyUser object
                    El usuario del cual consultar los administradores

                Returns
                ------
                queryset
                    Devuelve el queryset con los administradores del usuario

        """
        admins = AdminUser.objects.filter(usuarios=self)
        return admins


class AdminUser(MyUser):
    """ Clase utilizada para almacenar los usuarios administradores. Hereda los atributos de la clase MyUser"""
    usuarios = models.ManyToManyField(RegularUser, help_text="Selecciona los usuarios que administra", blank=True)
    class Meta:
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    @classmethod
    def create(cls):
        """ Método para crear usuarios con el campo is_staff a True

                Parameters
                ----------
                cls: AdminUser object
                    Nuevo objeto administrador

                Returns
                ------
                AdminUser
                    Devuelve el nuevo administrador

        """
        adminUser = cls(is_staff=True)
        adminUser.save()
        return adminUser


class Keyword(models.Model):
    """ Clase utilizada para almacenar las palabras clave utilizadas en el reconocimiento de voz"""
    id_keyword = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=20, unique=True, validators=[validate_keyword, alphabetic])
    usuario = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        """ Identificador de Django para nombrar el modelo

                        Parameters
                        ----------
                        self: Keyword objects
                            La palabra clave

                        Returns
                        ------
                        string
                            Devuelve el nombre de la palabra clave

                """
        return self.keyword


class ResizeImageSpec(ImageSpec):
    """ Clase utilizada para redimensionar las imagenes"""
    format = 'JPEG'
    opciones = {'quality': 100}
    processors = [Adjust(sharpness=1.1), ]

    @property
    def options(self):
        """ Propiedad que define las opciones del redimensionado de la imagen

                        Parameters
                        ----------
                        self: ImageSpec object
                            objeto ImageSpec

                        Returns
                        ------
                        dict
                            Diccionario de opciones

        """
        options = self.opciones
        # You can create some checks here and choose to change the options
        # you can access the file with self.source
        print("Tamaño del fichero: {0}".format(self.source.size))
        if self.source.size > 2 * 100 * 100:
            options['quality'] -= 25
        return options


class ResizeThumbnail(ImageSpec):
    """ Clase utilizada para generar thumbnails, hereda de la clase ImageSpec"""
    format = 'JPEG'
    opciones = {'quality': 90}
    processors = [Adjust(sharpness=1.1), ResizeToFill(600, 300), ]

    @property
    def options(self):
        """ Propiedad que define las opciones del redimensionado de la imagen

                                Parameters
                                ----------
                                self: ResizeThumbnail object
                                    objeto ResizeThumbnail

                                Returns
                                ------
                                dict
                                    Diccionario de opciones

        """
        options = self.opciones
        # You can create some checks here and choose to change the options
        # you can access the file with self.source
        print("Tamaño del fichero: {0}".format(self.source.size))
        if self.source.size > 2 * 100 * 100:
            options['quality'] -= 25
        return options


class Album(models.Model):
    """ Clase que se representa los álbumes almacenados en la aplicación"""
    id_album = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=40, null=False)
    descripcion = models.TextField(verbose_name='Descripción del Álbum', blank=True)
    thumbnail = ProcessedImageField(upload_to=get_upload_path, verbose_name="Portada", spec=ResizeThumbnail)
    address = map_fields.AddressField(max_length=200, verbose_name='Ubicación', blank=True,
                                      help_text="Añade información de la ubicación para localizar "
                                                "fotos basándote en el sitio donde fueron tomadas. Asombroso verdad")
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
        """ Sobrescribe el método save del modelo. Antes de guardar un objeto Album, generamos un slug, que pueda
            ser utilizado para generar URLs sencillas. Si existen dos álbumes con el mismo título, agregamos el
            nombre del administrador a la URL

                Parameters
                ----------
                self: Album object
                    objeto Album que va a ser guardado
                * args: argumentos posicionales
                ** kwargs: argumentos keywords

                Returns
                    No devuelve nada
                ------


        """
        qs = Album.objects.all()
        if qs.filter(titulo=self.titulo).exists():
            self.slug = slugify(self.titulo+' de '+self.created_by.username)
        else:
            self.slug = slugify(self.titulo)
        super(Album, self).save(*args, **kwargs)

    def thumbnail_tag(self):
        """ Genera una previsualización de la imagen, utilizada en el admin.py

                        Parameters
                        ----------
                        self: Album object
                            objeto Album


                        Returns
                        ------
                        string
                            Cadena con formato HTML

                """
        if (self.thumbnail):
            return mark_safe('<img src="/media/%s" width="150" height="150" />' % (self.thumbnail))

    thumbnail_tag.short_description = 'Portada'
    thumbnail_tag.allow_tags = True

    def get_n_elements(self):
        """ Devuelve el número de elementos del álbum
                        Parameters
                        ----------
                        self: Album object
                            objeto Album


                        Returns
                        ------
                        int
                            número de elementos del álbum (videos e imágenes)

                """
        return self.imagen_set.count() + self.video_set.count()

    get_n_elements.short_description = "Número de elementos"
    get_n_elements.allow_tags = True

@receiver(post_save, sender=Album)
def add_geolocation(sender, instance, created, **kwargs):
    """ Señal Django que se ejecuta después de guardar un objeto Álbum. Añade la dirección del álbum al diccionario de
        palabras y al archivo de gramática del decoder.

                    Parameters
                    ----------
                    sender: Album object
                        modelo que ejecuta el signal
                    instance
                        instancia del modelo Álbum que va a ser procesado
                    created
                        True si la instancia es un nuevo objeto o False en caso de que se esté modificando
                    ** Kwargs
                        Argumentos variables clave-valor

                    Returns
                    ------
                        No devuelve nada

            """
    if instance.address != "":
        ubicacion = instance.address.split(',')[0].lower()
        words = ubicacion.split(' ')
        for word in words:
            is_registered = check_dictionary(word)
            if not is_registered:
                add_keyword_to_dict(word)
                print("La palabra {0} no está registrada en el diccionario.".format(word))
        if len(words) > 1:
            update_grammar('(' + ubicacion + ')', True)
        else:
            update_grammar(ubicacion, True)


class Multimedia(models.Model):
    """ Clase abstracta de Python que representa los elementos Multimedia de la aplicación. """
    titulo = models.CharField(max_length=80, blank=True, null=True)
    descripcion = models.TextField(blank=True, help_text='Descríbeme...', verbose_name="Descripción")
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')
    keyword = models.ManyToManyField('Keyword', verbose_name="Palabras clave",
                                     help_text="Selecciona las palabras clave para etiquetar.")

    class Meta:
        abstract = True

    def get_admin_name(self):
        """ Función para obtener el usuario administrador propietario del elemento multimedia
                    Parameters
                    ----------
                     self: Multimedia object
                        objeto Multimedia


                    Returns
                    ------
                    string
                        nombre de usuario del administrador propietario del álbum

        """
        return self.album.created_by

    def get_album_title(self):
        """ Función para obtener el título del álbum del objeto multimedia
                    Parameters
                    ----------
                        self: Multimedia object
                        objeto Multimedia


                    Returns
                    ------
                    string
                        título del álbum

        """
        return self.album.titulo


class Imagen(Multimedia):
    """Clase que representa las imágenes del sistema. Hereda los atributos de la clase abstracta Multimedia"""
    image_width = models.PositiveSmallIntegerField(default=640, verbose_name='Anchura de la imagen')
    image_height = models.PositiveSmallIntegerField(default=480, verbose_name=' Altura de la imagen')
    fichero_imagen = models.ImageField(verbose_name= 'Archivo de imagen',
                                       upload_to=get_upload_path,
                                       help_text="Suba una imagen")
    thumbnail = ImageSpecField(source='fichero_imagen',
                               processors=[ResizeToFill(600, 300)],
                               format='JPEG',
                               options={'quality': 60})

    class Meta:
        verbose_name_plural = "Imágenes"

    def __str__(self):
        return self.titulo

    def filename(self):
        """ Función para obtener el nombre del archivo de imagen
                            Parameters
                            ----------
                                self: Imagen object
                                objeto Imagen


                            Returns
                            ------
                            string
                                nombre del archivo de imagen

                """
        return os.path.basename(self.fichero_imagen.name)

    def get_exif_data(self):
        """ Función para obtener los metadatos de las imágenes

                            Parameters
                            ----------
                                self: Imagen object
                                objeto Imagen


                            Returns
                            ------
                            dict
                                diccionario de metadatos

                """
        img = PILImage.open(self.fichero_imagen)
        if img._getexif() != None:
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            return exif
        return None

    def image_tag(self):
        """ Genera una previsualización de la imagen, utilizada en el admin.py

                        Parameters
                        ----------
                        self: Imagen object
                            objeto Imagen


                        Returns
                        ------
                        string
                            Cadena con formato HTML

                """
        return mark_safe('<img src="/media/users/%s/albums/%s/fotos/%s" width="150" height="150" />' % (self.get_admin_name(), self.album.titulo,  self.image))

    image_tag.short_description = 'Imagen'


    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Sobreescribe el método Save de la Imagen. Se utiliza para asignar el titulo de la imagen y los metadatos.
            Comprime la imagen si el tamaño de la imagen sobrepasa los 1.5 MB. Este parámetro se puede modificar.
                        Parameters
                        ----------
                        self: Imagen object
                            objeto Imagen
                        force_insert:
                            bool
                        force_update:
                            bool
                        using:
                            Database
                        update_fields:
                            fields

                        Returns
                        ------
                        No devuelve nada


                """
        if self.titulo is None:
            self.titulo = self.fichero_imagen.name.rstrip('.jpg')
        if self.get_exif_data() is not None:
            try:
                fecha = self.get_exif_data()['DateTime']
                if fecha:
                    fe = fecha.split(' ')[0].replace(':', '-')
                    cha = fecha.split(' ')[1]
                    fecha = fe + ' ' + cha
                    self.fecha_creacion = dateutil.parser.parse(fecha)
            except:
                fecha = datetime.now()

                if self.pk is None:
                    #TODO: Esto entra en un buble infinito...
                    if self.fichero_imagen.size > 1521440:         # 1.5 MB
                        while self.fichero_imagen.size > 2621440:
                            self.fichero_imagen = compress(self.fichero_imagen)
                            super(Imagen, self).save()

        super(Imagen, self).save()

    def image_tag(self):

        if self.fichero_imagen:
            return mark_safe('<img src="/media/%s" width="150" height="150" />' % self.fichero_imagen)

    image_tag.short_description = 'Imagen'
    image_tag.allow_tags = True


class Video(Multimedia):
    """Clase que representa los vídeos del sistema. Hereda los atributos de la clase abstracta Multimedia"""
    fichero_video = models.FileField(verbose_name="Archivo de Vídeo",
                                     upload_to=get_upload_path,
                                     validators=[validate_file_extension])

    class Meta:
        verbose_name_plural = "Videos"

    def __str__(self):
        return self.titulo

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Sobreescribe el método Save del Video. Se utiliza para asignar el titulo del video

                                Parameters
                                ----------
                                self: Imagen object
                                    objeto Video
                                force_insert:
                                    bool
                                force_update:
                                    bool
                                using:
                                    Database
                                update_fields:
                                    fields

                                Returns
                                ------
                                No devuelve nada


                        """
        if self.titulo is None:
            self.titulo = self.fichero_video.name
        super(Video, self).save()


class Radio(models.Model):
    """Clase que representa las emisoras de radio del sistema."""
    nombre = models.CharField(verbose_name="Nombre", max_length=100, blank=False)
    url = models.URLField(verbose_name="URL de la Radio")
    thumbnail = models.ImageField(verbose_name="Carátula de la Radio",
                                  upload_to='thumbs/radios', null=True, blank=True)
    frecuencia = models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)
    keyword = models.ManyToManyField('Keyword', help_text="Selecciona las palabras clave para etiquetar.")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Emisoras de radio"
        verbose_name_plural = verbose_name
        ordering = ['frecuencia']

    def image_tag(self):
        """ Genera una previsualización de la imagen, utilizada en el admin.py

                                Parameters
                                ----------
                                self: Radio object
                                    objeto Radio


                                Returns
                                ------
                                string
                                    Cadena con formato HTML

                        """
        return mark_safe('<img src="/media/%s" width="100" height="100" />' % (self.thumbnail))

    image_tag.short_description = 'Carátula'


class RFIDMiddleware(models.Model):
    """ Clase utilizada para gestionar el inicio de sesión mediante RFID"""
    user = models.ForeignKey(RegularUser, on_delete=models.CASCADE, blank=True, null=True)
    token = models.CharField(max_length=25)
    rfid_id = models.CharField(max_length=12)
    timestamp = models.DateTimeField(auto_now_add=True)
