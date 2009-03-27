# -*- coding: utf8 -*-

"""
Biblioteca para armar y leer los índices.

Se usa desde server.py para consulta, se utiliza directamente
para crear el índice.
"""

from __future__ import with_statement

import cPickle
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
import shutil

from whoosh import store, index
from whoosh.fields import Schema, STORED, ID, KEYWORD, TEXT
from whoosh.qparser import QueryParser, MultifieldParser

usage = """Indice de títulos de la CDPedia

Para generar el archivo de indice hacer:

  cdpindex.py fuente destino [max] [dirbase]

    fuente: archivo con los títulos
    destino: en donde se guardará el índice
    max: cantidad máxima de títulos a indizar
    dirbase: de dónde dependen los archivos
"""

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
    html = open(arch, "r").read()
    m = SACATIT.match(html)
    if m:
        tit = m.groups()[0]
    else:
        tit = u"<sin título>"
    return tit

def _getPalabrasHTML(arch):
    arch = os.path.abspath(arch)
    cmd = config.CMD_HTML_A_TEXTO % arch
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    txt = p.stdout.read()
    txt = txt.decode("utf8")
    return txt

class Index(object):
    '''Maneja todo el índice.

    La idea es ofrecer funcionalidad, después vemos tamaño y tiempos.
    '''

    def __init__(self, filename, verbose=False):
        if verbose:
            print "Abriendo el índice"
        filename + ".whoosh"
        storage = store.FileStorage(filename)
        schema = Schema(titulo=TEXT(stored=True), contenido=TEXT(stored=False),
                        nomhtml=ID(stored=True), docid=ID)
        self.index = index.Index(storage, schema=schema)

    def listar(self):
        '''Muestra en stdout las palabras y los artículos referenciados.'''
        id_shelf = self.id_shelf
        for palabra, docid_ptje in sorted(self.word_shelf.items()):
            docids = [x[0] for x in docid_ptje] # le sacamos la cant
            print "%s: %s" % (palabra, [id_shelf[str(x)][1] for x in docids])

    def listado_valores(self):
        '''Devuelve la info de todos los artículos.'''
        return sorted(self.id_shelf.values())

    def listado_palabras(self):
        '''Devuelve las palabras indexadas.'''
        return sorted(self.word_shelf.keys())

    def get_random(self):
        '''Devuelve un artículo al azar.'''
        return random.choice(self.id_shelf.values())

    def _merge_results(self, results):
        # vemos si tenemos algo más que vacio
        results = filter(bool, results)
        if not results:
            return []

        # el resultado final es la intersección de los parciales ("and")
        intersectados = reduce(operator.iand, (set(d) for d in results))
        final = {}
        for result in results:
            for pagtit, ptje in result.items():
                if pagtit in intersectados:
                    final[pagtit] = final.get(pagtit, 0) + ptje

        final = [(pag, tit, ptje) for (pag, tit), ptje in final.items()]
        return sorted(final, key=operator.itemgetter(2), reverse=True)


    def search(self, words):
        '''Busca palabras completas en el índice.'''
        searcher = self.index.searcher()
        fields = ["contenido", "titulo"]
        parser = MultifieldParser(fields, schema = self.index.schema)
        query = parser.parse(words)
        results = searcher.search(query)
        return results

    def detailed_search(self, words):
        '''Busca palabras parciales en el índice.'''
        searcher = self.index.searcher()
        fields = ["contenido", "titulo"]
        parser = MultifieldParser(fields, schema = self.index.schema)
        detailed = []
        for field in fields:
            for word in words.split():
                detailed.append(parser.make_wildcard(field, "*"+word+"*"))
        query = parser.make_or(detailed)
        print query
        results = searcher.search(query)
        return results

    @classmethod
    def create(cls, filename, fuente, verbose):
        '''Crea los índices.'''
        arch = filename + ".whoosh"
        if os.path.exists(arch):
            shutil.rmtree(arch)
        os.makedirs(arch)

        storage = store.FileStorage(arch)
        schema = Schema(titulo=TEXT(stored=True), contenido=TEXT(stored=False),
                        nomhtml=ID(stored=True), docid=ID)
        # creamos el indice
        ix = index.Index(storage, schema=schema, create=True)

        writer = ix.writer()
        # fill them
        for docid, (nomhtml, titulo, palabras_texto) in enumerate(fuente):
            if verbose:
                print "Agregando al índice [%r]  (%r)" % (titulo, nomhtml)
            writer.add_document(titulo=titulo.decode('utf-8'), docid=unicode(docid), nomhtml=unicode(nomhtml), contenido=palabras_texto)
        # grabamos
        writer.commit()
        return docid


def generar_de_html(dirbase, verbose, full_text=True):
    # lo importamos acá porque no es necesario en producción
    from src import utiles

    def gen():
         fh = codecs.open(config.LOG_PREPROCESADO, "r", "utf8")
         fh.next() # título
         for i,linea in enumerate(fh):
             partes = linea.split()
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
                     palabras = []
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
