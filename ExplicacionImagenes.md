¡Ahora la cdpedia tiene imágenes!

Las URLs de las imágenes se sacan de los htmls, y se escriben en un archivo en el temp, y luego se pasa a bajarlas de la web y dejarlas en un directorio también en el temp pero que no se limpia todas las veces.

Las imágenes llevan un procesamiento distinto que todo el resto de la cdpedia, porque no las tenemos de entrada en el disco, sino que hay que bajarlas de la web, entonces no las queremos borrar todas las veces, y por eso ese directorio no se limpia. Incluso ahora tenemos una utilidad nueva (utilities/descargarImagenes.py), de manera que uno puede cortar el generar.py, y seguir bajando imágenes durante varias veces con este utilitario, y sólo relanzar el generar.py una vez que tengamos todas las imágenes en el disco (tener en cuenta que cuando la imagen esá en el disco, la misma no se vuelve a bajar...).

Además, aunque hoy por hoy estamos armando el CD con las imágenes como las bajamos, seguramente el día de mañana no se hará así, sino que se achicarán algunas un poco. Como el juego de "cuanto achicar y cuales" será un poco interactivo, no es que bajamos la imagen y la grabamos ya achicada en el directorio final.

Entonces, el proceso con respecto a las imágenes sería algo como...

  1. Se ejecuta el generar.py y eso nos escribe un imagenes.txt en el temp, y pasa a descargarlas (supongamos que lo cortamos acá por X razón).

  1. Ejecutamos descargaImagenes.py para que siga (y lo cortamos, y volvemos a ejecutarlo cuanto sea suficiente).

  1. Ya descargado todo, volvemos a ejecutar el generar.py, que vuelve a hacer todo, pero como las imágenes ya están descargadas apenas tarda ahí... y termina de hacer todo.