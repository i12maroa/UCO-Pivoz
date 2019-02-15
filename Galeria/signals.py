from django.db.models.signals import post_save
from django.dispatch import receiver
from Galeria.models import Keyword
from Galeria.views import decoder
from Galeria.SpeechDetector import GRAMMAR
from Galeria.views import start_new_thread

@start_new_thread
@receiver(post_save, sender=Keyword)
def update_grammar(sender, instance, **kwargs):
    decoder.set_grammar("grammar", GRAMMAR)