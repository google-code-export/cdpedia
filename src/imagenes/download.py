# -*- coding: utf8 -*-

from __future__ import with_statement

import codecs
import os
import urllib2
import threading
import Queue

import config

HEADERS = {'User-Agent':
    'Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.5) Gecko/2008121622 '
    'Ubuntu/8.10 (intrepid) Firefox/3.0.5'
}

def _descargar(url, fullpath, msg):
    # descargamos!
    basedir, _ = os.path.split(fullpath)
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    req = urllib2.Request(url.encode("utf8"), headers=HEADERS)
    u = urllib2.urlopen(req)
    content_length = u.headers.get("content-length")
    if content_length is None:
        msg("  %?? KB")
    else:
        largo = int(content_length) / 1024.0
        msg("  %d KB" % round(largo))

    img = u.read()
    with open(fullpath, "wb") as fh:
        fh.write(img)
    msg("  ok!")


def traer(verbose):
    errores = {}
    lista_descargar = []

    # vemos cuales tuvieron problemas antes
    log_errores = os.path.join(config.DIR_TEMP, "imagenes_neterror.txt")
    if os.path.exists(log_errores):
        with codecs.open(log_errores, "r", "utf8") as fh:
            imgs_problemas = set(x.strip() for x in fh)
    else:
        imgs_problemas = set()

    for linea in codecs.open(config.LOG_IMAGENES, "r", "utf8"):
        linea = linea.strip()
        if not linea:
            continue

        arch, url = linea.split(config.SEPARADOR_COLUMNAS)
        fullpath = os.path.join(config.DIR_TEMP, "images", arch)

        if url not in imgs_problemas and not os.path.exists(fullpath):
            lista_descargar.append((url, fullpath))

    def msg(*t):
        if verbose:
            print " ".join(str(x) for x in t)

    queue = Queue.Queue(40)
    errqueue = []

    def worker():
        while True:
            # extraer tarea de la cola, reconocer fin de secuencia
            ent = queue.get()
            if ent is None:
                break
            url, fullpath = ent
            del ent
            
            for retries in xrange(3):
                try:
                    _descargar(url, fullpath, msg)
                    break
                except urllib2.HTTPError, err:
                    msg("  error %d!" % err.code)
                    errores[err.code] = errores.get(err.code, 0) + 1
                    errqueue.append(url)
                    break
                except Exception, e:
                    print "Uh...", e
            
    workers = [ threading.Thread(target=worker) for i in xrange(4) ]

    try:
        for worker in workers:
            worker.start()
            
        tot = len(lista_descargar)
        for i, (url, fullpath) in enumerate(lista_descargar):
            print "Descargando (%d/%d)  %s" % (i, tot, url)
            queue.put((url, fullpath))
    finally:
        # do this even on KeyboardInterrupt
        # (or other errors)
        for worker in workers:
            queue.put(None)

        for worker in workers:
            worker.join()

        with codecs.open(log_errores, "a", "utf8") as fh:
            for url in errqueue:
                fh.write(url + "\n")

    if errores:
        print "WARNING! Tuvimos errores:"
        for code, cant in errores.items():
            print "       %d %5d" % (code, cant)
