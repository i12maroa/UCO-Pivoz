#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pocketsphinx import *
import os
from celery import shared_task
from PiVoz.settings import BASE_DIR


MODEL_DIR = os.path.join(BASE_DIR, 'Speech/model')
GRAMMAR = os.path.join(BASE_DIR, 'Speech/model/grammar.jsgf')


class SpeechDetector:
    """A decoder class to initialite decoder with the properly configuration and decode Speech"""

    def __init__(self):
        """ Initialize default parameters """
        config = Decoder.default_config()
        config.set_string('-hmm', os.path.join(MODEL_DIR, 'es-adapt'))
        config.set_string('-dict', os.path.join(MODEL_DIR, 'es.dict'))
        config.set_string('-lm', os.path.join(MODEL_DIR, 'es-20k.lm.bin'))
        self.decoder = Decoder(config)


    def set_search(self, search_method):
        """ Set the search method. It must be grammar, keyword_spotting"""
        try:
            self.decoder.set_search(search_method)
        except:
            raise ValueError("Error en set_search: No se ha podido establecer el método %s." % search_method)

    def set_keyword_spotted(self, keyphrase="pivoz"):
        """ Set the keyword to be spoke in order to wake_up the recognition. Defaults to pivoz."""
        try:
            self.decoder.set_keyphrase("keyword", keyphrase)
        except:
            raise ValueError("Error en set_keyword_spotted: No se ha podido establecer la palabra clave %s." % keyphrase)


    def set_grammar(self, grammar_name, path_to_file):
        if os.path.isfile(path_to_file):
            self.decoder.set_jsgf_file(grammar_name, path_to_file)  # Default will be GRAMMAR path
        else:
            raise FileNotFoundError("No se encuentra el fichero {0}".format(path_to_file + '/' + grammar_name))

    def get_search_method(self):
        return self.decoder.get_search()

    def decode_phrase(self, wav_file):
        """ Decode the wav_file and return the phrase recognized"""
        self.decoder.start_utt()
        stream = open(os.path.join('/Users/tony/PiVoz/media/', wav_file), "rb")
        while True:
            buf = stream.read(1024)
            if buf:
                self.decoder.process_raw(buf, False, False)
            else:
                break
        self.decoder.end_utt()

    def get_hyp(self):
        try:
            if self.decoder.hyp().hypstr != "":
                return self.decoder.hyp().hypstr
        except:
            return ""


