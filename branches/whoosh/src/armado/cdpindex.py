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

from whoosh import store, index, tables
from whoosh.fields import Schema, STORED, ID, KEYWORD, TEXT
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StandardAnalyzer

usage = """Indice de títulos de la CDPedia

Para generar el archivo de indice hacer:

  cdpindex.py fuente destino [max] [dirbase]

    fuente: archivo con los títulos
    destino: en donde se guardará el índice
    max: cantidad máxima de títulos a indizar
    dirbase: de dónde dependen los archivos
"""


STOP_WORDS = frozenset(("de", "a", "y", "es", "en", "este",
                        "vos", "para", "ser", "o", "si", "puede", "son"
                        "eso", "con", "como", "desde", "un", "no"))

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
        storage = FileStorage(filename)
        schema = Index.get_schema()
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
        results = searcher.search(query)
        return results

    @classmethod
    def get_schema(cls):
        """ crea el Schema de whoosh. """
        analyzer = StandardAnalyzer(stoplist = STOP_WORDS)
        # definimos el esquema, en este caso es similar a lo que se guardaba
        # antes en el pickle.
        # podiramos:
        #   1) agregar 'phrase=True' al title
        #   2) usar NGRAM en lugar de TEXT en caso de que nos sea util
        #   3) user el tipo KEYWORD (habria que sacar estos tags del html)
        schema = Schema(titulo=TEXT(analyzer=analyzer, stored=True),
                        contenido=TEXT(analyzer=analyzer, stored=False),
                        nomhtml=STORED)
        return schema

    @classmethod
    def create(cls, filename, fuente, verbose):
        '''Crea los índices.'''
        if os.path.exists(filename):
            shutil.rmtree(filename)
        os.makedirs(filename)
        storage = FileStorage(filename)
        # creamos el indice
        ix = index.Index(storage, schema=cls.get_schema(), create=True)

        from src.utiles import ProgressSpinner
        # fill them
        progress = ProgressSpinner()
        with ix.writer() as writer:
            for nomhtml, titulo, palabras_texto, ptje in fuente:
                progress.next()
                if verbose:
                    print "Agregando al índice [%r]  (%r)" % (titulo, nomhtml)
                writer.add_document(titulo=titulo,
                                    nomhtml=nomhtml.encode('utf-8'),
                                    contenido=palabras_texto)
        progress.finish()
        ix.optimize()
        return ix.doc_count()


def generar_de_html(dirbase, verbose, full_text):
    # lo importamos acá porque no es necesario en producción
    from src import utiles
    from src.preproceso import preprocesar

    def gen():
        fileNames = preprocesar.get_top_htmls(config.LIMITE_PAGINAS)

        for i, (dir3, arch, puntaje) in enumerate(fileNames):
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
            yield (nomhtml, titulo, palabras, puntaje)

    cant = Index.create(config.PREFIJO_INDICE, gen(), verbose)
    return cant


class FileStorage(store.FileStorage):
    """ Subclase de store.FileStorage que setea la compresión al máximo """

    def create_table(self, name, **kwargs):
        f = self.create_file(name)
        # actualizamos kwargs con compressed == 9
        kwargs.update(dict(compressed=9))
        return tables.TableWriter(f, **kwargs)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print usage
        sys.exit()

    tini = time.time()
    cant = _create_index(*sys.argv[1:])
    delta = time.time()-tini
    print "Indice creado! (%.2fs)" % delta
    print "Archs: %d  (%.2f mseg/arch)" % (cant, 1000*delta/cant)
