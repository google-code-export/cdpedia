# Actualización del contenido de la Wikipedia #

Ya tengo un mirror funcionando. Las primeras pruebas dan que la exportacion completa a HTML llevaría unas 3000 horas de procesamiento en un sempron, unos 4 meses.

Ordenaré mis notas para resumir el procedimiento. (7/7/10)


---

La idea es actualizar el ultimo dump estatico disponible que es de junio de 2008.

Como alternativa, se evalúa la posibilidad de reactivar la rama de la generación dinámica a partir del xml que se genera cada dos semanas.

Voy a llevar aca un log detallado de las pruebas que voy haciendo y recibiendo comentarios que ayuden a resolver.


# Detalles #

(Borrador de trabajo, apunte de referencia, hay mucho mas todavía)


  1. Bajé el último dump.
  1. Busqué los métodos que usan para exportar e importar los dumps [6](6.md), con la idea de replicar exactamente el procedimiento utilizado previamente para la generación del html estático.
  1. El problema consistía en realizar una importación sin problemas de el ultimo dump xml () a una instalación de mediawiki sobre un lamp, que funcione correctamente, y aparentemente desde alli (con tiempo y paciencia) se podría extraer el html estatico sin problemas.

---

  1. Esto implicaba hacer una instalación de mediawiki adecuada, reconstruir la Wikipedia en español en el servidor de pruebas a partir de el ultimo xml disponible, y generar el dump del html estático a partir de ese mirror local utilizando la misma herramienta que se utilizó para generar los html estáticos previos.
  1. Empecé todo el trabajo en mi notebook, y a pesar de que dispuse el espacio en disco necesario para la operación, al ver que había problemas con los resultados y también cuales eran los tiempos de procesamiento, los tiempos que arrojaban las operaciones se hacian muy largos para pensar en hacer varias pruebas, por lo cual replique la instalación en otra máquina con mas espacio y mas potencia (después leería buscando con google que se había tardado 40 dias para hacer el ultimo dump de la version en inglés, y encontrar algunos reportes de bug).
  1. Instalé una tercera para poder hacer pruebas en paralelo. Como el objetivo era obtener el archivo de resultado una vez, no se trabajó inicialmente en definir un procedimiento determinado para hacerlo, confiando en que la documentación permitiría reproducir un procedimiento bien definido para realizar el procedimiento.
    1. Sin embargo los problemas en los resultados obligaron a reproducir el proceso documentando el detalle de la configuración de las pruebas realizadas a fin de localizar el problema y encontrar o desarrollar una solución.
  1. Con ese fin configuré un server desde cero, con el home en un disco nuevo de 1 terabyte, para olvidarme de los problemas de espacio, con el reciente Ubuntu 10.04 en 64 bits para mi viejo sempron 1150 con 4 g de ram. (Una vez aislados los problemas de configuración, podía replicar los procesos en la otra maquina con 2 athlon si necesitaba mas procesadores)
  1. Hice todas las configuraciones necesarias con los valores por default.
  1. Rastree posibles configuraciones alternativas publicadas.
  1. Cambié la configuración requerida por mediawiki según (referenciar)
  1. Descarté importDUMP.php según [6](6.md) dado el tamaño del trabajo (igual hice una prueba)
  1. Probé con importDump.php tomando en cuenta [9](9.md)
  1. Probé con mwdumper. Fuciono la importacion y la exportacion sin reportar errores. Al revisar el resultado aparecian paginas mal renderizadas o corruptas, que rastreando, ya estaban asi en la mediawiki local que se uso para el trabajo. Se verifico con dump reader que esos articulos se veian bien, asi como en la Wikipedia online.
  1. Hice distintas pruebas en distintas maquinas con la misma configuración. El consumo de tiempo y procesamiento es enorme, asi como el espacio en disco que requiere, por lo cual terminé montando un servidor especificamente para esto, sobre un disco nuevo de 1 tera para no tener problemas de espacio.
  1. Encontré que en la documentacion de mwdumper decía que los ultimos dumps habia que procesarlos con la version actual del codigo, no con los binarios disponibles.
  1. Compilé la ultima version de mwdumper, que se supone comipila con gjc, pero daba 89 warnings. Revisando los docs, recomendaban la version de java y recompilé con eso (no, siguió compilando con gjc, ver configuración).
  1. Hice la prueba con la nueva versión. En este caso, para aislar y rastrear el problema, no voy a enviar el pipe directamente al mysql, sino guardar el sql para poder analizarlo. Si el problema era al importar, no tendría que volver a generarlo. La primera corrida resultó en lo siguiente(start 2010-05-13 0:55):

---

hernan@ServerKamaj:~/mwdumper/build$ mwdumper --format=sql:1.5 eswiki-20100331-pages-articles.xml > dump.sql
1.000 pages (36,496/sec), 1.000 revs (36,496/sec)
2.000 pages (36,258/sec), 2.000 revs (36,258/sec)
3.000 pages (36,491/sec), 3.000 revs (36,491/sec)
4.000 pages (36,099/sec), 4.000 revs (36,099/sec)
5.000 pages (36,729/sec), 5.000 revs (36,729/sec)
6.000 pages (37,421/sec), 6.000 revs (37,421/sec)
7.000 pages (38,346/sec), 7.000 revs (38,346/sec)
8.000 pages (39,808/sec), 8.000 revs (39,808/sec)
Exception in thread "main" java.io.IOException: required character (got U+20): ';'
> > at org.mediawiki.importer.XmlDumpReader.readDump(mwdumper)
> > at org.mediawiki.dumper.Dumper.main(mwdumper)
Caused by: org.xml.sax.SAXParseException: required character (got U+20): ';'
> > at gnu.xml.stream.SAXParser.parse(libgcj.so.10)
> > at javax.xml.parsers.SAXParser.parse(libgcj.so.10)
> > at javax.xml.parsers.SAXParser.parse(libgcj.so.10)
> > at org.mediawiki.importer.XmlDumpReader.readDump(mwdumper)
> > ...1 more
Caused by: javax.xml.stream.XMLStreamException: required character (got U+20): ';'
> > at gnu.xml.stream.XMLParser.error(libgcj.so.10)
> > at gnu.xml.stream.XMLParser.require(libgcj.so.10)
> > at gnu.xml.stream.XMLParser.readCharData(libgcj.so.10)
> > at gnu.xml.stream.XMLParser.next(libgcj.so.10)
> > at gnu.xml.stream.SAXParser.parse(libgcj.so.10)
> > ...4 more

---

Este error no había aparecido en las pruebas que realicé antes utilizando los binarios precompilados. (Igual no estoy conforme con como funcionó la compilación, tuvo varios warnings que deberia revisar, en verdad deberia trabajar con un binario sin warnings. Tengo que revisar ese procedimiento, y ver mejor el estado actual de mw)

De todos modos ya vi un reporte sobre problemas con algunos caracteres en los titulos del archivo, y como solucionarlo. Y voy a revisar de nuevo mis configuraciones tomando en cuenta los reportes sobre problemas de codificación de caracteres y configuración (En todo el stack). Y también particularmente, con juegos de caracteres en las Wikipedias no en inglés.

Mientras veo de corregir la compilacion, pruebo con otro binario sin gui que anda mejor pero igual se plancha:

---

```
775.000 pages (1.809,184/sec), 775.000 revs (1.809,184/sec)
776.000 pages (1.809,318/sec), 776.000 revs (1.809,318/sec)
777.000 pages (1.809,792/sec), 777.000 revs (1.809,792/sec)
778.000 pages (1.810,342/sec), 778.000 revs (1.810,342/sec)
Exception in thread "main" java.lang.IllegalArgumentException: Invalid contributor
	at org.mediawiki.importer.XmlDumpReader.closeContributor(Unknown Source)
	at org.mediawiki.importer.XmlDumpReader.endElement(Unknown Source)
	at org.apache.xerces.parsers.AbstractSAXParser.endElement(Unknown Source)
	at org.apache.xerces.parsers.AbstractXMLDocumentParser.emptyElement(Unknown Source)
	at org.apache.xerces.impl.XMLDocumentFragmentScannerImpl.scanStartElement(Unknown Source)
	at org.apache.xerces.impl.XMLDocumentFragmentScannerImpl$FragmentContentDispatcher.dispatch(Unknown Source)
	at org.apache.xerces.impl.XMLDocumentFragmentScannerImpl.scanDocument(Unknown Source)
	at org.apache.xerces.parsers.XML11Configuration.parse(Unknown Source)
	at org.apache.xerces.parsers.XML11Configuration.parse(Unknown Source)
	at org.apache.xerces.parsers.XMLParser.parse(Unknown Source)
	at org.apache.xerces.parsers.AbstractSAXParser.parse(Unknown Source)
	at org.apache.xerces.jaxp.SAXParserImpl$JAXPSAXParser.parse(Unknown Source)
	at org.apache.xerces.jaxp.SAXParserImpl.parse(Unknown Source)
	at javax.xml.parsers.SAXParser.parse(SAXParser.java:198)
	at org.mediawiki.importer.XmlDumpReader.readDump(Unknown Source)
	at org.mediawiki.dumper.Dumper.main(Unknown Source)
```

---

Esto del invalid contributor, esta reportado como bug https://bugzilla.wikimedia.org/show_bug.cgi?id=18328, estoy investigando las soluciones propuestas. Sucede cuando por motivos legales o de otro tipo fue necesario eliminar un contributor. Revisé el código, el tema es que queda como null, tal vez en esos casos deberia ponerse 'deleted' y como id algun codigo compatible.

Update: hice alguna pruebas minimas con las instrucciones que subieron (https://bugzilla.wikimedia.org/show_bug.cgi?id=18328) pero sigue dando error. Sigo rastreando el codigo java del mwdumper, si es el unico problema que queda deberia resolverse fácil.


---

# Sintesis de alternativas a explorar: #
  1. importDump (el de mediawiki, lento y no recomendado para gran tamaño)
  1. mwimport
  1. html2sql
  1. TeroDump
  1. DumpReader
  1. WikiTaxi
  1. WikiFilter
  1. wikiprep
  1. kiwix
  1. WikiReader
  1. Okawix



---

La otra alternativa es o bien pasar del xml al html directamente con alguna herramienta, o bien generar el html en forma dinámica. Estoy explorando las alternativas existentes para cada cosa, y tratando de aislar y documentar el problema para tratar de resolverlo. Ya leí la experiencia previa de Facundo al respecto, aunque lo primero que haré antes de hacer nada en esta rama es volver a revisarlo.

De todos modos hice algunas pruebas:
  1. Dump reader, aparentemente funciona sin problemas, lo usé para verificar que las paginas que yo veia mal en el html estático, que tambien estaban mal en mediawiki, se leian correctamente de ese mismo dump. Pero no genera el html original
  1. (Fast?) Offline Reader, no lo pude hacer funcionar de una, si es necesario probaré con las versiones con las que el reporta. Usa Django, un parser que parece discontinuado, y aparentemente se fueron resolviendo algunos bugs, incluyendo uno que tambien tenía que ver con los caracteres de idiomas diferentes al inglés.

  1. Probe algun otro que si tengo tiempo documentaré.


---

# Resumen situación actual: #

Para realizar la importacion a mediawiki, mwdumper convierte el xml a sql.
Separamos la generación de sql hasta verificar que funciona sin errores.

Se dispone de 2 versiones precompiladas, y el codigo fuente actual.

Las 2 versiones compiladas de mwdumper tienen problemas (diferentes) con el ultimo dump, reportados mas arriba.

La compilación a partir del source también, y además tiene 89 warnings que hay que revisar. La documentación dice que está probado con gjc 4, que es la que usamos (4.1), y recomienda el uso de la version sun si aparecen ciertos problemas. Falta probar la versión con sun.


---

# Alternativas pendientes de investigación, sugeridas por la comunidad: #


---

Sean Moss-Pultz <sean@openmoko.com>
para	"Alejandro J. Cura" <alecura@gmail.com>

Hi Alejandro

On Fri, Apr 30, 2010 at 11:43 PM, Alejandro J. Cura <alecura@gmail.com> wrote:



> [snip](snip.md)

> Hernán and Diego are the two interns tasked with updating the data
> that cdpedia uses to make the cd (it currently uses a static html dump
> dated June 2008), but they are encountering some problems while trying
> to make an up to date static html es-wikipedia dump.

> I'm ccing this list of people, because I'm sure you've faced similar
> issues when making your offline wikipedias, or because maybe you know
> someone who can help us.


We're doing this XML to HTML conversion as one of the steps in our process of rendering Wikipedia for our WikiReader device. We can build Spanish without issues.

All of our source code is here:

> http://github.com/wikireader/wikireader

The specific portion you would need is the offline-renderer located here:

> http://github.com/wikireader/wikireader/tree/master/host-tools/offline-renderer/

You'll probably need to modify the HTML output for your specific needs. Just let me know if you get stuck.

Sean




---

de	Manuel Schneider <manuel.schneider@wikimedia.ch>
para	dev-l@openzim.org
cc	"Alejandro J. Cura" <alecura@gmail.com>,
(...)

Hey,

have a look at Kiwix:

http://www.kiwix.org/index.php/Main_Page/es

As far as I know Emmanuel (maintainer of Kiwix) has made ZIM files for es:wp.

Alternatively here is a description how to make them:
http://www.kiwix.org/index.php/Tools/en
(http://www.kiwix.org/index.php/Tools/es - not complete)

/Manuel

---

de	Pascal Martin <pmartin@linterweb.fr>
para	dev-l@openzim.org,
Samuel Klein <meta.sj@gmail.com>
cc	ibarrags@gmail.com,
Jimmy Wales <jwales@wikia-inc.com>,
Madeleine Ball <mad@printf.net>,
Facundo Batista <facundobatista@gmail.com>,
Wiki-offline-reader-l@wikimedia.org,
Offline Wikireaders <wikireader@lists.laptop.org>,
Cecilia Sagol <csagol@educ.gov.ar>,
Pomies Patricia <ppomies@educ.gov.ar>,
Patricio Lorente <patricio.lorente@gmail.com>,
Enrique Chaparro <cinabrium@gmail.com>,
Sean Moss-Pultz <sean@openmoko.com>,
Kul Takanao Wadhwa <kwadhwa@wikimedia.org>,
Emmanuel Engelhart <emmanuel.engelhart@wikimedia.fr>,
godiard@gmail.com,
Diego Mascialino <dmascialino@gmail.com>,
Hernan Olivera <lholivera@gmail.com>,
cjb@laptop.org,
Iris Fernández <irisfernandez@gmail.com>,
OpenZim devel <dev-l@openzim.org>
fecha	1 de mayo de 2010 09:11
asunto	Re: [dev-l](openZIM.md) a DVD with the Spanish Wikipedia (was [Argentina](Argentina.md)WikiBrowse improvements)

ocultar detalles 1 may (hace 12 días)

Hello,

you could test our solution also :
http://www.okawix.com/

If you want we could make .iso ready to use.


---

De [18](18.md):

---

[Bug 18694](https://code.google.com/p/cdpedia/issues/detail?id=8694) - Spanish wikipedia XML dump problems
Summary: 	Spanish wikipedia XML dump problems
Status: 	ASSIGNED
Product: 	Wikimedia
Component: 	Downloads
Version: 	unspecified
Platform: 	All All
Importance: 	Normal normal with 5 votes (vote)
Assigned To: 	Tomasz Finc
URL:
Keywords:
Depends on:
Blocks:
> Show dependency tree / graph



Reported: 	2009-05-06 09:15 UTC by elephantus\_l
Modified: 	2010-05-03 11:33 UTC (History)
CC List: 	7 users (show)

See Also:

Attachments
Add an attachment (proposed patch, testcase, etc.)

Description elephantus\_l 2009-05-06 09:15:58 UTC

I downloaded two sequential Spanish wikipedia XML dump files
(eswiki-20090504-pages-articles.xml.bz2 and before that
eswiki-20090421-pages-articles.xml.bz2). When I imported the file into wikitaxi
it showed a strange error on a large number of pages: the titles and the
content of the pages were mixed-up, that is, the title would be something and
the text itself would obviously be from a different page (or it would be a
combination of two pages). So I looked into the original XML file itself and
this is what I found, for example:

> 

&lt;page&gt;


> > 

&lt;title&gt;

Gómez Plata

&lt;/title&gt;


> > 

&lt;id&gt;

454035

&lt;/id&gt;


> > 

&lt;revision&gt;


> > > 

&lt;id&gt;

25156038

&lt;/id&gt;


> > > 

&lt;timestamp&gt;

2009-03-28T06:38:04Z

&lt;/timestamp&gt;


> > > 

&lt;contributor&gt;


> > > > 

&lt;username&gt;

SajoR

&lt;/username&gt;


> > > > 

&lt;id&gt;

130444

&lt;/id&gt;



> > > 

&lt;/contributor&gt;


> > > 

&lt;minor /&gt;


> > > 

&lt;comment&gt;

leve mejora

&lt;/comment&gt;


> > > <text xml:space="preserve">'''Montserrat Domínguez''' ([[Madrid](Madrid.md)],
[[1963](1963.md)]) es una [[periodismo|periodista]] [[España|española]].

Considera que la primera obligación de un periodista es ser crítico con el
poder y es optimista respecto a la situación actual del periodismo. Su trabajo
le ofrece, en su opinión, &quot;un motor de vida&quot;.

Es aficionada a la [[lectura](lectura.md)] y a los viajes.

## Biografía ##

Estudió [[de la Información](Ciencias.md)] por la [[Universidad Complutense de
Madrid]]. Posteriormente cursó un Master en Periodismo por la [[Universidad de
Columbia]].


So the title of the page is Gómez Plata (a municipality in Colombia), but the
page is about a Spanish journalist.

This didn't happen when I downloaded other wikipedia dumps (en, de, nl, sv).
Could someone please look into this problem? Thank you.

Comment 1 Tomasz Finc 2009-05-06 23:58:15 UTC

I can indeed find this in eswiki-20090504-pages-articles.xml.bz2 but not in
eswiki-20090504-pages-meta-current.xml which is bizarre. A quick look at things
didn't showcase any big errors in the code. This is going to to take a bit more
time to find. Thank you for testing the other dumps to see if this was
happening as well.

Comment 2 elephantus\_l 2009-05-07 06:46:39 UTC

Apparently the messed-up pages are those with a timestamp from approximately
mid-January 2009 to mid- or late-April 2009. The pages older or younger than
that aren't affected.

Comment 3 Tomasz Finc 2009-05-26 08:41:52 UTC

It doesn't seem to affect all articles within that time range though making it
a bit hard to find other examples. Can you give me a list of 10
or so more that are still affected in the latest dump 20090519. Gómez Plata got
updated and is now dumping correctly.

Comment 4 Tomasz Finc 2009-06-29 07:42:52 UTC

**[Bug 19420](https://code.google.com/p/cdpedia/issues/detail?id=9420) has been marked as a duplicate of this bug.**

Comment 5 Platonides 2009-07-10 21:33:20 UTC

eswiki-20090702-pages-articles is still affected.

For instance,
[[MediaWiki:anonnotice]] have the content of [[Iglesias](Carlos.md)].

[[Wikipedia:Portada]] has

> 

&lt;page&gt;


> > 

&lt;title&gt;

Wikipedia:Portada

&lt;/title&gt;


> > 

&lt;id&gt;

2271189

&lt;/id&gt;


> > 

&lt;revision&gt;


> > > 

&lt;id&gt;

25284089

&lt;/id&gt;


> > > 

&lt;timestamp&gt;

2009-04-02T13:56:29Z

&lt;/timestamp&gt;


> > > 

&lt;contributor&gt;


> > > > 

&lt;username&gt;

Muro de Aguas

&lt;/username&gt;


> > > > 

&lt;id&gt;

214907

&lt;/id&gt;



> > > 

&lt;/contributor&gt;


> > > 

&lt;minor /&gt;


> > > 

&lt;comment&gt;

wapedia no es propiedad de wikipedia

&lt;/comment&gt;


> > > <text xml:space="preserve">#REDIRECT [[Plantilla:Ficha de
militar]]

Unknown end tag for &lt;/text&gt;



> > 

&lt;/revision&gt;



> 

&lt;/page&gt;



whereas that revision is
http://es.wikipedia.org/w/index.php?title=Wikipedia:Portada&diff=25284089&oldid=24586619

Has a clean dump**been done since the problem was detected?**

**A dump not based on the previous one.**

Comment 6 Platonides 2009-07-11 00:13:10 UTC

(In reply to comment #2)
> Apparently the messed-up pages are those with a timestamp from approximately
> mid-January 2009 to mid- or late-April 2009. The pages older or younger than
> that aren't affected.

Could it be a slave whose autoincrement column desynchonized?

Comment 7 Enrique 2009-07-13 13:26:11 UTC

eswiki-20090710-pages-articles.xml resolves this error???

Comment 8 Platonides 2009-07-13 13:31:46 UTC

No. But you can use the pages-meta-current to skip it.

Comment 9 Enrique 2009-07-13 13:55:34 UTC

them, this error will not  have solution?
tomorrow i will try with pages-meta-current to skip it error, but I prefer wait
for an solution.

Comment 10 Alejandro Tejada Capellan 2009-07-17 19:51:41 UTC

(In reply to comment #8)
> No. But you can use the pages-meta-current to skip it.
Ok, is not too much problem to download 1GB instead of
758MB, but Could someone find any hint in the PHP code that creates this
backup, that actually explains why this error is ocurring only in the Spanish
Wikipedia and not in the English version?
I had verified that English version database backup does not show these errors.

Comment 11 Enrique 2009-07-17 20:37:19 UTC

Hi, i downloaded pages-meta-current to skip it error, but i see many red links,
in the official wikipedia these links are blue
many of templates are empty or uncategorised.

Comment 12 Tomasz Finc 2009-07-21 01:55:29 UTC

(In reply to comment #10)
> (In reply to comment #8)
> > No. But you can use the pages-meta-current to skip it.
> Ok, is not too much problem to download 1GB instead of
> 758MB, but Could someone find any hint in the PHP code that creates this
> backup, that actually explains why this error is ocurring only in the Spanish
> Wikipedia and not in the English version?

Sadly we've suffered a loss of a good chunk of our previously run snapshots so
comparing to
those will be a bit hard. If I can catch the problem happening actively then it
will be much
easier.

Comment 13 Brion Vibber 2009-08-07 19:50:44 UTC

**[Bug 20114](https://code.google.com/p/cdpedia/issues/detail?id=0114) has been marked as a duplicate of this bug.**

Comment 14 Platonides 2010-01-10 22:34:41 UTC

**[Bug 19598](https://code.google.com/p/cdpedia/issues/detail?id=9598) has been marked as a duplicate of this bug.**

Comment 15 Ascánder Suárez 2010-02-25 07:25:52 UTC

Hi, this problem is still present in the backups of the Spanish Wikipedia. It
is hard to calculate the number of articles affected, but they are among those
modified between January and April 2009. No affected articles have been
observed so far out of this range of time.

Articles affected (i.e. articles showing a wrong content in the periodic
backups including the last published one:
eswiki-20100221-pages-articles.xml.bz2) seem to be the same in different
backups.

Here are some examples of wrong content:

Article [[:es:Escudo de la Polinesia Francesa]] shows contents belonging to
[[:es:Anexo:Gobernadores de Corrientes]]

Article [[:es:Pleurodema]] shows contents belonging to [[:es:Aviación virtual]]

Redirect [[:es:Candelilla]] points to [[:es:Eugène Scribe]] instead of
[[:es:Euphorbia antisyphilitica]].

Redirect [[:es:Knut Schreiner]] points to [[:es:Euphorbia antisyphilitica]]
instead of [[:es:Euroboy]]

Here is an upper bound to the number of articles affected (i.e. articles
updated between January and April 2009): 44193 articles/annexes, 5634 files on
other space names and 99067 redirects. Contrary to articles, redirects are easy
to check and I can say that almost all of them show a wrong content in the last
backup.
For instance, these are the redirects updated on the first hour of March first,
2009 and they are all wrong:

'Aeropuerto de Ontario' --> 'Agustín de Pedrayes'
'Corno' --> 'El aprendiz de brujo (Dukas)'
'Kenneth Burrell' --> 'Aeropuerto Internacional LA/Ontario'
'Oro amarillo' --> 'Emo'
'Claro de Luna (Beethoven)' --> 'oro'
'Claro de Luna (Maupassant)' --> 'Sonata para piano n.º 14 (Beethoven)'
'Claro de luna (Debussy)' --> 'Sonata para oboe y piano (Poulenc)'
'Idioma retorromance' --> 'Adrenalynn'
'Boubacar traoré' --> 'Suite bergamasque'
'Rodrigo Sepúlveda Lara' --> 'Claro de luna (astronomía)'
'Oxnard' --> 'Rodrigo Sepúlveda'

Comment 16 Ascánder Suárez 2010-03-24 10:44:32 UTC

This problem is vanishing.

As mentioned before, pages affected are among those edited for the last time
between January 2009 and April 2009, so with the help of
[[:es:Usuario:Boticario]] and his bot CEM-bot, the pages with these
characteristics were reviewed first orthographically and then the remaining for
cosmetic changes. There are still several pages and redirects that show a wrong
contents in the las dump, with and upper bound of 38 redirects and 16260 pages.

All of the 38 remaining redirects contain character "_" in their title and
thus, are not accessible through the site._

In order to finish with this problem and unless someone proposes a better idea,
I'll suggest Boticario to edit them introducing a useless space at the end of
the first line or something equally useless and invisible.

For the record, here is the list of redirects that I don't know how to access
(notice the underscores in their title):

_[[:es:A **c]]** [[:es:A_d]]
**[[:es:A _e_c]]** [[:es:Siglo\_II\_d._C.]]
**[[:es:La\_440]]** [[:es:S._I.]]
_[[:es:580\_a.**C.]]** [[:es:589\_a._C.]]
_[[:es:588\_a.**C.]]** [[:es:585\_a._C.]]
_[[:es:584\_a.**C.]]** [[:es:582\_a._C.]]
_[[:es:594\_a.**C.]]** [[:es:600\_a._C.]]
_[[:es:559\_a.**C.]]** [[:es:556\_a._C.]]
_[[:es:550\_a.**C.]]** [[:es:558\_a._C.]]
_[[:es:555\_a.**C.]]** [[:es:551\_a._C.]]
_[[:es:546\_a.**C.]]** [[:es:529\_a._C.]]
_[[:es:528\_a.**C.]]** [[:es:526\_a._C.]]
_[[:es:525\_a.**C.]]** [[:es:522\_a._C.]]
_[[:es:521\_a.**C.]]** [[:es:520\_a._C.]]
_[[:es:510\_a.**C.]]** [[:es:515\_a._C.]]
_[[:es:K.**O.]]** [[:es:Brasilia,_D.**F.]]
_[[:es:Brasilia, D._F.]]** [[:es:1200\_a.**C.]]
_[[:es:500\_a._C.]]** [[:es:Marina de EE.**UU.]]
_[[:es:Francis S._Collins]]**

Comment 17 Platonides 2010-03-24 22:00:15 UTC

Look at
http://es.wikipedia.org/w/index.php?title=Francis_S.%C2%A0Collins&diff=prev&oldid=25984099
It is not an space, it is a non-breaking space. This redirect was created by a
indef blocked vandal which used a no breaking space (0xc2 0xa0) instead of the
normal one (0x20).

For some reason action=view is treating the 160 space as a 32 one and thus
doesn't find it.
We have 73 articles like that. Most were made by Rosarino, but also by
Gunderson, Muro Bot, Wiki Winner and Jtspotau.
We should probably delete them.

Comment 18 Platonides 2010-03-25 15:11:02 UTC

I opened [bug 22939](https://code.google.com/p/cdpedia/issues/detail?id=2939) to handle the nbsp titles.

Comment 19 Steef 2010-05-03 11:33:37 UTC

It seems that not only eswiki is affected by this.

There is a report on dewiki Village Pump about this issue on dewikisource
(http://de.wikipedia.org/w/index.php?title=Wikipedia:Fragen_zur_Wikipedia&oldid=73896610#Dump).





---


## Seleccion de las referencias utilizadas ##

De [2](2.md):

---

NOTE: Dumps are curerntly halted due to [Bug 23264](https://code.google.com/p/cdpedia/issues/detail?id=3264)

---


De [5](5.md):

---

What happened to the SQL dumps?

In mid-2005 we upgraded the Wikimedia sites to MediaWiki 1.5, which uses a very different database layout than earlier versions. SQL dumps of the 'cur' and 'old' tables are no longer available because those tables no longer exist.

We don't provide direct dumps of the new 'page', 'revision', and 'text' tables either because aggressive changes to the backend storage make this extra difficult: much data is in fact indirection pointing to another database cluster, and deleted pages which we cannot reproduce may still be present in the raw internal database blobs. The XML dump format provides forward and backward compatibility without requiring authors of third-party dump processing or statistics tools to reproduce our every internal hack. If required, you can use the mwdumper tool (see below) to produce SQL statements compatible with the version 1.4 schema from an XML dump.

De [6](6.md):

---

Using importDump.php, if you have shell access

> Recommended method for general use, but slow for very big data sets. For very large amounts of data, such as a dump of a big Wikipedia, use mwdumper, and import the links tables as separate SQL dumps.

importDump.php is a command line script located in the maintenance folder of your MediaWiki installation. If you have shell access, you can call importdump.php like this:

php importDump.php 

&lt;dumpfile&gt;



where 

&lt;dumpfile&gt;

 is the name of the XML dump file. If the file is compressed and that has a .gz or .bz2 file extension, it is decompressed automatically.

Note Note: to run importDump.php (or any other tool from the maintenance directory), you need to set up your AdminSettings.php file.

Note Note: running importDump.php can take quite a long time. For a large Wikipedia dump with millions of pages, it may take days, even on a fast server. Also note that the information in meta:Help:Import about merging histories, etc. also applies.

After running importDump.php, you may want to run rebuildrecentchanges.php in order to update the content of your Special:Recentchanges page.

---



# Links #

**[1](1.md) http://en.wikipedia.org/wiki/Wikipedia_database**


**[2](2.md) http://static.wikipedia.org/**


**[3](3.md) https://bugzilla.wikimedia.org/show_bug.cgi?id=23264**


[4](4.md) http://dumps.wikimedia.org/eswiki/20100331/

[5](5.md) http://meta.wikimedia.org/wiki/Data_dumps

[6](6.md) http://www.mediawiki.org/wiki/Manual:Importing_XML_dumps

[7](7.md) http://www.mediawiki.org/wiki/Manual:System_administration

[8](8.md) http://www.mediawiki.org/wiki/Special:Export

[9](9.md) http://www.mediawiki.org/wiki/Manual:AdminSettings.php

[10](10.md)http://meta.wikimedia.org/wiki/Help:Import

[11](11.md) http://www.mediawiki.org/wiki/Installation

[12](12.md) http://www.mediawiki.org/wiki/Manual:Installation_guide

[13](13.md) http://meta.wikimedia.org/wiki/Requests_for_dumps

[14](14.md) http://www.zedwood.com/article/145/cpp-convert-wikipedia-xml-dump-to-mysql-utf8-safe

[15](15.md) http://mundo-n900.blogspot.com/2010/04/wikipedia-offline-en-tu-n900.html

[16](16.md) http://users.softlab.ece.ntua.gr/~ttsiod/buildWikipediaOffline.html

[17](17.md) http://en.wikipedia.org/wiki/Wikipedia_database#Dynamic_HTML_generation_from_a_local_XML_database_dump

[18](18.md) https://bugzilla.wikimedia.org/show_bug.cgi?id=18694

[19](19.md) http://www.mediawiki.org/wiki/Manual:MWDumper

[20](20.md) http://myy.helia.fi/~karte/tero-dump/

[21](21.md) http://www.mediawiki.org/wiki/Manual_talk:MWDumper

[22](22.md) http://meta.wikimedia.org/wiki/Help:Import

[23](23.md) http://www.mediawiki.org/wiki/Manual:AdminSettings.php

[24](24.md) https://launchpad.net/wikipediadumpreader

[25](25.md) http://arunxjacob.wordpress.com/2008/01/29/installing-wikipedia-part-2-of-n-getting-the-data/

(este listado deberia ser en orden alfabético)
Add your content here.  Format your content with:
  * Text in **bold** or _italic_
  * Headings, paragraphs, and lists
  * Automatic links to other wiki pages