# -*- coding: utf8 -*-

'''Algunas pequeñas funciones útiles.'''

import config

import re
import sys


# Coincide si se empieza con uno de los namespaces más ~
RE_NAMESPACES = re.compile(r'(%s)~(.*)' % '|'.join(config.NAMESPACES))

def separaNombre(nombre):
    '''Devuelve (namespace, resto) de un nombre de archivo del wiki.'''
    m = RE_NAMESPACES.match(nombre)
    if not m:
        result = (None, nombre)
    else:
        result = m.groups()
    return result


class ProgressSpinner(object):
    """Un spinner *muy* simple para mostrar actividad en la terminal"""

    def __init__(self, out=sys.stdout):
        """inicializa el spinner"""
        self.out = out
        self.running = True
        def spinner_generator():
            while self.running:
                for i in ('|', '/', '-', '\\', '|', '/', '-', '\\'):
                    yield i
        self.spinner = spinner_generator()

    def next(self):
        self.out.write('\r%s' % self.spinner.next())

    def finish(self):
        self.running = False
        self.out.write('\r')


