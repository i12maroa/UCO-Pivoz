# Validators.py

import os
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.mp4', '.ogg']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Unsupported file extension.')

def validate_keyword(keyword):
    reserved_keys = ['todos', 'todas', 'mostrar', 'muestra', 'ver', 'enseña', 'abre', 'siguiente', 'anterior', 'adelante', 'atras', 'subirvolumen', 'bajarvolumen', 'videos', 'fotos', 'imagenes', 'fotografias', 'play', 'pause']
    if keyword.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u") in reserved_keys:
        raise ValidationError(u'La palabra clave "' + keyword + '" es una palabra reservada. Por favor, elige otra palabra clave.')
    if ' ' in keyword:
        raise ValidationError(u'La palabra clave no debe contener espacios en blanco. Si necesita añadir una frase puede hacerlo introduciendo palabra por palabra en el campo <<Palabra Clave>>.')