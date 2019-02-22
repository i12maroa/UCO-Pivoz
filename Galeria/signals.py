from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from Galeria.models import Keyword
from Galeria.tasks import remove_keyword
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

