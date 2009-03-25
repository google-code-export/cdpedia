# -*- coding: utf8 -*-

"""
Biblioteca para armar y leer los índices.

Se usa desde server.py para consulta, se utiliza directamente
para crear el índice.
"""

from __future__ import with_statement

import time
import sys
import os
import codecs
import random
import unicodedata
import operator
import glob
import config
import subprocess
import re
import sqlite3

usage = """Indice de títulos de la CDPedia

Para generar el archivo de indice hacer:

  cdpindex.py fuente destino [max] [dirbase]

    fuente: archivo con los títulos
    destino: en donde se guardará el índice
    max: cantidad máxima de títulos a indizar
    dirbase: de dónde dependen los archivos
"""

BASETIT = "/cdpedia.db"
BASEFTS = "/cdpedia_fts.db"

# Buscamos todo hasta el último guión no inclusive, porque los
# títulos son como "Zaraza - Wikipedia, la enciclopedia libre"
SACATIT = re.compile(".*?<title>([^<]*)\s+-", re.S)

# separamos por palabras
PALABRAS = re.compile("\w+", re.UNICODE)

def normaliza(txt):
    '''Recibe una frase y devuelve sus palabras ya normalizadas.'''
    txt = unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').lower()
    return txt

def _getHTMLTitle(arch):
    # Todavia no soportamos redirect, asi que todos los archivos son
    # válidos y debería tener TITLE en ellos
    html = codecs.open(arch, "r", "utf8").read()
    m = SACATIT.match(html)
    if m:
        tit = m.groups()[0]
    else:
        tit = u"<sin título>"
    return tit

def _getPalabrasHTML(arch):
    arch = os.path.abspath(arch)
    cmd = "lynx -nolist -dump -display_charset=UTF-8 %s" % arch
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    txt = p.stdout.read()
    txt = txt.decode("utf8")
    return txt

class Index(object):
    '''Maneja todo el índice.

    La idea es ofrecer funcionalidad, después vemos tamaño y tiempos.
    '''

    def __init__(self, filename, verbose=False):
        self.db_titulos = sqlite3.connect( filename + BASETIT )
        self.db_fts = sqlite3.connect( filename + BASEFTS )
        self.db_titulos.execute('PRAGMA synchronous = OFF;')
        self.db_fts.execute('PRAGMA synchronous = OFF;')

    def listar(self):
        '''Muestra en stdout las palabras y los artículos referenciados.'''
        id_shelf = self.id_shelf
        for palabra, docid_ptje in sorted(self.word_shelf.items()):
            docids = [x[0] for x in docid_ptje] # le sacamos la cant
            print "%s: %s" % (palabra, [id_shelf[str(x)][1] for x in docids])

    def search(self, keywords):
        ret = []
        cur = self.db_fts.cursor()
        cur.execute("SELECT name, title FROM page WHERE page MATCH ?",
                   (keywords,))
        print "search '%s'" % keywords
        for row in cur:
            ret.append((row[0], row[1], "50"))
        return ret
    
    def detailed_search(self, words):
        ret= []
        keywords = []
        for word in words.split():
          keywords.append(word + "*")
          keywords.append('AND')
        keywords.pop()
        print "detailed search '%s'" % keywords
        cur =  self.db_fts.cursor()
        cur.execute("SELECT name, title FROM page WHERE page MATCH ?", (' '.join(keywords),))
        for row in cur:
          ret.append((row[0], row[1], "50"))
        return ret

    def listado_valores(self):
        ret = []
        cur = self.db_titulos.cursor()
        cur.execute("SELECT name, title FROM page", ())
        for row in cur:
            ret.append((row[0], row[1]))
        return ret

    def listado_palabras(self):
        return []

    def get_random(self):
        return random.choice(self.listado_valores())

    @classmethod
    def create(cls, filename, fuente, verbose):
        db_titulos = sqlite3.connect( filename + BASETIT )
        db_titulos.execute('PRAGMA synchronous = OFF;')
        db_titulos.execute("CREATE VIRTUAL TABLE page USING FTS3 (name ,title);")
        db_fts = sqlite3.connect( filename + BASEFTS )
        db_fts.execute( "PRAGMA synchronous = OFF;" )
        db_fts.execute("CREATE VIRTUAL TABLE page USING FTS3 (name ,title,"
                      "content);")
        for docid, (nomhtml, titulo, palabras_texto) in enumerate(fuente):
            if verbose:
                print "Agregando a la base [%r]  (%r)" % (titulo, nomhtml)
            db_titulos.execute("INSERT INTO page VALUES (?,?)",(nomhtml, titulo))
            db_fts.execute("INSERT INTO page VALUES (?,?,?)", ( nomhtml, titulo,
                          palabras_texto ))

        db_titulos.commit()
        db_fts.commit()
        return docid

# Lo dejamos comentado para despues, para hacer el full_text desde los bloques
#
# def generar(src_info, verbose, full_text=False):
#     return _create_index(config.LOG_PREPROCESADO, config.PREFIJO_INDICE,
#                         dirbase=src_info, verbose=verbose, full_text=full_text)
#
#     def gen():
#         fh = codecs.open(fuente, "r", "utf8")
#         fh.next() # título
#         for i,linea in enumerate(fh):
#             partes = linea.split()
#             arch, dir3 = partes[:2]
#             if not arch.endswith(".html"):
#                 continue
#
#             (categoria, restonom) = utiles.separaNombre(arch)
#             if verbose:
#                 print "Indizando [%d] %s" % (i, arch.encode("utf8"))
#             # info auxiliar
#             nomhtml = os.path.join(dir3, arch)
#             nomreal = os.path.join(dirbase, nomhtml)
#             if os.access(nomreal, os.F_OK):
#                 titulo = _getHTMLTitle(nomreal)
#                 if full_text:
#                     palabras = _getPalabrasHTML(nomreal)
#                 else:
#                     palabras = []
#             else:
#                 titulo = ""
#                 print "WARNING: Archivo no encontrado:", nomreal
#
#             # si tenemos max, lo respetamos y entregamos la info
#             if max is not None and i > max:
#                 raise StopIteration
#             yield (nomhtml, titulo, palabras)
#
#     cant = Index.create(salida, gen(), verbose)
#     return cant

def generar_de_html(dirbase, verbose, full_text=True):
    # lo importamos acá porque no es necesario en producción
    from src import utiles

    def gen():
        fh = codecs.open(config.LOG_PREPROCESADO, "r", "utf8")
        fh.next() # título
        for i,linea in enumerate(fh):
            partes = linea.split(config.SEPARADOR_COLUMNAS)
            arch, dir3 = partes[:2]
            if not arch.endswith(".html"):
                continue

            (categoria, restonom) = utiles.separaNombre(arch)
            if verbose:
                print "Indizando [%d] %s" % (i, arch.encode("utf8"))
            # info auxiliar
            nomhtml = os.path.join(dir3, arch)
            nomreal = os.path.join(dirbase, nomhtml)
            if os.access(nomreal, os.F_OK):
                titulo = _getHTMLTitle(nomreal)
                if full_text:
                  palabras = _getPalabrasHTML(nomreal)
                else:
                  palabras = u""
            else:
                titulo = ""
                print "WARNING: Archivo no encontrado:", nomreal

            # si tenemos max, lo respetamos y entregamos la info
            if max is not None and i > max:
                raise StopIteration
            yield (nomhtml, titulo, palabras)

    cant = Index.create(config.PREFIJO_INDICE, gen(), verbose)
    return cant

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print usage
        sys.exit()

    tini = time.time()
    cant = _create_index(*sys.argv[1:])
    delta = time.time()-tini
    print "Indice creado! (%.2fs)" % delta
    print "Archs: %d  (%.2f mseg/arch)" % (cant, 1000*delta/cant)
