# -*- coding: utf-8 -*-

import os
import re
import urllib
import urlparse
import posixpath
from mimetypes import guess_type

import utils
import bmp
import config
from src.armado import compresor
from src.armado import cdpindex
from src.armado import to3dirs
from destacados import Destacados
from utils import TemplateManager
from src import third_party # Need this to import werkzeug
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect

WATCHDOG_IFRAME = '<iframe src="/watchdog/update" style="width:1px;height:1px;'\
                  'display:none;"></iframe>'
NOTFOUND = u"""
El artículo '%s' no pudo ser incluido en el disco <br/><br>
Podés acceder al mismo en Wikipedia en
<a class="external" href="%s">este enlace</a> externo.
"""
ALL_ASSETS = config.ASSETS + ["images",  "extern", "tutorial"]
if config.EDICION_ESPECIAL is not None:
    ALL_ASSETS.append(config.EDICION_ESPECIAL)

class CDPedia(object):

    def __init__(self, conf=None):
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.template_manager = TemplateManager(template_path)
        self._art_mngr = compresor.ArticleManager()
        self._img_mngr = compresor.ImageManager()
        self._destacados_mngr = Destacados(self._art_mngr, debug=False)

        self.index = cdpindex.IndexInterface(config.DIR_INDICE)
        self.index.start()

        self.url_map = Map([
            Rule('/', endpoint='main_page'),
            Rule('/wiki/<nombre>', endpoint='articulo'),
            Rule('/al_azar', endpoint='al_azar'),
            Rule('/images/<path:nombre>', endpoint='imagen'),

        ])

    def on_imagen(self, request, nombre):
        try:
            normpath = posixpath.normpath(nombre)
            asset_data = self._img_mngr.get_item(normpath)
        except Exception, e:
            msg = u"Error interno al buscar contenido: %s" % e
            return InternalServerError(msg)
        if asset_data is None:
            print "WARNING: no pudimos encontrar", repr(nombre)
            try:
                width, _, height = request.args["s"].partition('-')
                width = int(width)
                height = int(height)
            except Exception, e:
                return InternalServerError("Error al generar imagen")
            img = bmp.BogusBitMap(width, height)
            return Response(img.data, mimetype="img/bmp")
        type_ = guess_type(nombre)[0]
        return Response(asset_data, mimetype=type_)


    def on_main_page(self, request):
        msg = u"CDPedia v" + config.VERSION
        portales = self.render_template("portales")
        data_destacado = self._destacados_mngr.get_destacado()
        if data_destacado is not None:
            link, titulo, primeros_parrafos = data_destacado
            pag = self.render_template("mainpage", mensaje=msg, link=link,
                                       titulo=titulo,
                                       primeros_parrafos=primeros_parrafos,
                                       portales=portales)
        else:
            pag = self.render_template("mainpage_sin_destacado", mensaje=msg,
                                       portales=portales)
        r = self._wrap_content(pag, title="Portada")
        return Response(r, mimetype='text/html')

    def on_articulo(self, request, nombre):
        orig_link = utils.get_orig_link(nombre)
        try:
            data = self._art_mngr.get_item(nombre)
        except Exception, e:
            return InternalServerError(u"Error interno al buscar contenido: %s" % e)

        if data is None:
            return NotFound(NOTFOUND % (nombre, orig_link))

        title = utils.get_title_from_data(data)
        r = self._wrap_content(data, title, orig_link=orig_link)
        return Response(r, mimetype='text/html')

    #@ei.espera_indice
    def on_al_azar(self, request):
        link, tit = self.index.get_random()
        link = u"wiki/" + to3dirs.from_path(link)
        return redirect(urllib.quote(link.encode("utf-8")))

    def _wrap_content(self, contenido, title, orig_link=None):
        header = self.render_template("header", titulo=title, iframe=WATCHDOG_IFRAME)

        if orig_link is None:
            orig_link = ""
        else:
            orig_link = u'Si tenés conexión a Internet, podés visitar la '\
                        u'<a class="external" href="%s">página original y '\
                        u'actualizada</a> de éste artículo.'  % orig_link

        footer = self.render_template("footer", orig_link=orig_link)
        return header + contenido + footer

    def render_template(self, template_name, **context):
        t = self.template_manager.get_template(template_name)
        for key in context.iterkeys():
            data = context[key]
            if isinstance(data, unicode):
                context[key] = data.encode("utf-8")
        r = t.substitute(**context)
        return r

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app(with_static=True):
    app = CDPedia()
    if with_static:
        paths = [("/"+path, os.path.join(config.DIR_ASSETS, path)) for path in ALL_ASSETS]
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, dict(paths))
    return app

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app()
    run_simple('127.0.0.1', 8000, app, use_debugger=True, use_reloader=False)
