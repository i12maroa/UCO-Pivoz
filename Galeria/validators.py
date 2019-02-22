# Validators.py

import os
import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

alphabetic = RegexValidator(r'^[a-zA-Z]*$', 'Por favor, introduzca una valor correcto. Solo se permiten carácteres alfabéticos a-zA-Z ')

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.mp4', '.ogg']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')

def validate_keyword(keyword):
    keyword = keyword.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    vocales = re.findall(r'[aeiou]+', keyword, re.IGNORECASE)
    consonantes = re.findall(r'[bcdfghjklmnpqrstvwxyz]+', keyword, re.IGNORECASE)
    reserved_keys = ['todos', 'todas', 'mostrar', 'muestra', 'ver', 'enseña', 'abre', 'siguiente', 'anterior', 'adelante', 'atras', 'subirvolumen', 'bajarvolumen', 'videos', 'fotos', 'imagenes', 'fotografias', 'play', 'pause']
    if keyword in reserved_keys:
        raise ValidationError(u'La palabra clave "' + keyword + '" es una palabra reservada. Por favor, elige otra palabra clave.')
    for subs in consonantes:
        if len(subs) > 4:
            raise ValidationError(u'La palabra clave "' + keyword + '" no tiene sentido.')
    for subs in vocales:
        if len(subs) > 3:
            raise ValidationError(u'La palabra clave "' + keyword + '" no tiene sentido.')

    if ' ' in keyword:
        raise ValidationError(u'La palabra clave no debe contener espacios en blanco. Si necesita añadir una frase puede hacerlo introduciendo palabra por palabra en el campo <<Palabra Clave>>.')