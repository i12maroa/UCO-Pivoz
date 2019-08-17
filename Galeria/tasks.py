from __future__ import unicode_literals, absolute_import
from celery import shared_task
from Galeria.SpeechDetector import MODEL_DIR
import io
import shutil
import os


# ---------------------------------------- CELERY TASKS ---------------------------------------- #
#                                                                                                #
#                 Lista de tareas que serán ejecutadas por Celery de forma asíncrona.            #
#                                                                                                #
#                                                                                                #
#                                                                                                #
#  ----------------------------------------------------------------------------------------------#

def check_dictionary(word):
    file = io.open(os.path.join(MODEL_DIR, 'es.dict'), "r", encoding="utf-8")
    encontrado = 0
    if (file != FileNotFoundError):
        for line in file:
            if (word == line.split(" ")[0]):
                encontrado = 1
                break
        file.close()
        return encontrado
    else:
        raise IOError("No se ha encontrado ningún diccionario. Póngase en contacto con el administrador.")


@shared_task
def add_keyword_to_dict(keyword):
    """Aquí es necesario realizar una conversión de las palabras con el fin de crear los fonemas.
    Las reglas de conversión son:
    - C por K ---> casa por k a s a
    - C por Z ---> tercero por t e r z e r o
    - V por B ---> televisión por t e l e b i s i o n
    - G por J ---> tragedia por t r a j e d i a
    - CC por KZ -> traducción por t r a d u k z i o n
    """
    file = io.open(os.path.join(MODEL_DIR, 'es.dict'), "a", encoding="utf-8")
    if file != FileNotFoundError:
        keyword = keyword.lower()
        if keyword[0] == 'h':
            spell = keyword[1:]
        spell = keyword.replace("ce", "ze").replace("ci", "zi"). \
            replace("v", "b"). \
            replace("ge", "je").replace("gi", "ji"). \
            replace("cc", "zk").replace("c", "k"). \
            replace("sh", "s"). \
            replace("que", "ke").replace("qui", "ki"). \
            replace("ñ", "gn"). \
            replace("güi", "gui"). \
            replace("güe", "gue"). \
            replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("c h", "ch")
        file.write(keyword + " ")
        for c in spell:
            file.write(c + " ")
        file.write("\n")
        file.close()
    else:
        raise IOError("No se ha encontrado ningún diccionario. Póngase en contacto con el administrador.")


@shared_task
def update_grammar(keyword, geolocation=False):
    """Función para actualizar el fichero de gramática con las nuevas palabras clave o ubicaciones"""
    keyword = keyword.lower()
    file = io.open(os.path.join(MODEL_DIR, 'grammar.jsgf'), "r", encoding="utf-8")
    tmpfile = io.open(os.path.join(MODEL_DIR, 'grammar.jsgf.tmp'), "w", encoding="utf-8")
    tag = '<keyTag>'
    if geolocation:
        tag = '<ubication>'
    if file != FileNotFoundError:
        for line in file:
            if line.startswith(tag) and line.find(keyword) == -1:
                # Si es la primera linea no escribo el separador
                if line.endswith("()*;"):
                    tmpfile.write(line[:-4] + keyword + ")*;\n")
                else:
                    tmpfile.write(line[:-4] + " | " + keyword + ")*;\n")
            else:
                tmpfile.write(line)
        file.close()
        tmpfile.close()
        shutil.copy(tmpfile.name, file.name)
        os.remove(os.path.join(MODEL_DIR, 'grammar.jsgf.tmp'))
    else:
        raise IOError("No se ha encontrado ningún diccionario. Póngase en contacto con el administrador.")

@shared_task
def remove_keyword(keyword):
    """ Función asíncrona para borrar las palabras clave del fichero de gramática"""
    keyword = keyword.lower()
    file = io.open(os.path.join(MODEL_DIR, 'grammar.jsgf'), "r", encoding="utf-8")
    tmpfile = io.open(os.path.join(MODEL_DIR, 'grammar.jsgf.tmp'), "w", encoding="utf-8")
    if file != FileNotFoundError:
        for line in file:
            if line.startswith('<keyTag>'):
                line = line.replace(" | " + keyword, "")
            tmpfile.write(line)
        file.close()
        tmpfile.close()
        shutil.copy(tmpfile.name, file.name)
        os.remove(os.path.join(MODEL_DIR, 'grammar.jsgf.tmp'))
    else:
        raise IOError("No se ha encontrado ningún diccionario. Póngase en contacto con el administrador.")
