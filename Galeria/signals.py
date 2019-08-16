from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from Galeria.models import Keyword, Album, Imagen
from Galeria.tasks import add_keyword_to_dict, update_grammar, check_dictionary
import logging
from django.db.models import signals
from Galeria.views import decoder
from Galeria.SpeechDetector import GRAMMAR
from Galeria.views import start_new_thread

# @start_new_thread
# @receiver(post_save, sender=Keyword)
# def update_grammar(sender, instance, **kwargs):
#     decoder.set_grammar("grammar", GRAMMAR)

logger = logging .getLogger(__name__)


@receiver(post_save, sender=Keyword)
def remove_signal(sender, instance, **kwargs):
    logger.info(
        'Signal remove_keyword on post_delete for model: %s and row id %s',
        sender._meta.db_table,
        instance.keyword
    )
    try:
        remove_keyword(instance.keyword)
    except:
        pass


@receiver(post_save, sender=Keyword)
def print_keyword(sender, instance, created, **kwargs):
    print("Entra signal")
    if created:
        print("created" + instance.keyword)



@receiver(post_save, sender=Imagen)
def update_title(sender, instance, created, **kwargs):
    print("Entra post Sginal")
    if created and instance.titulo is None:
        new_title = instance.fichero_imagen.url.split('/')[4]
        instance.titulo = new_title
        print(new_title)
        instance.save()

