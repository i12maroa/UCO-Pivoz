from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from Galeria.models import Keyword, Album, Imagen
from Galeria.tasks import remove_keyword
import logging


logger = logging .getLogger(__name__)


@receiver(post_delete, sender=Keyword)
def remove_signal(sender, instance, **kwargs):
    """ Señal que se ejecuta cada vez que se elimina una palabra clave para actualizar el fichero de gramática y el
     diccionario de palabras"""
    try:
        remove_keyword(instance.keyword)
    except:
        pass


@receiver(post_save, sender=Imagen)
def update_title(sender, instance, created, **kwargs):
    """ Si no hemos introducido un titulo a la imagen, asigna el nombre del archivo de imagen"""
    if created and instance.titulo is None:
        new_title = instance.fichero_imagen.url.split('/')[4]
        instance.titulo = new_title
        instance.save()

