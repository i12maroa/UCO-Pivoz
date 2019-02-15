#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pocketsphinx import *
import os
from celery import shared_task



MODEL_DIR = "/Users/tony/PiVoz/Speech/model"
GRAMMAR = "/Users/tony/PiVoz/Speech/model/grammar.jsgf"


# A decoder class to initialite decoder with the properly configuration and decode Speech
class SpeechDetector:

    def __init__(self):
        """ Initialize default parameters """
        config = Decoder.default_config()
        config.set_string('-hmm', os.path.join(MODEL_DIR, 'es-adapt'))
        config.set_string('-dict', os.path.join(MODEL_DIR, 'es.dict'))
        config.set_string('-lm', os.path.join(MODEL_DIR, 'es-20k.lm.bin'))
        self.decoder = Decoder(config)


    def set_search(self, search_method):
        try:
            self.decoder.set_search(search_method)
        except:
            raise ValueError("Error en set_search: No se ha podido establecer el método %s." % search_method)


    def set_grammar(self, grammar_name, path_to_file):
        if os.path.isfile(path_to_file):
            self.decoder.set_jsgf_file(grammar_name, path_to_file)  # Default will be GRAMMAR path

    def decode_phrase(self, wav_file):
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


