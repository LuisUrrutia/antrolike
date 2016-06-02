# coding=utf-8
from classes import Xenforo
import os.path
import json

SAVE_FILE = "./last.json"

# Obtiene ultimo ID a través de JSON guardado
start_id = 1
if os.path.isfile(SAVE_FILE):
    content = open(SAVE_FILE, 'r').read()
    data = None
    try:
        data = json.loads(content)
    except:
        start_id = 1

    if data is not None and 'id' in data:
        start_id = data['id']
        try:
            start_id = int(start_id)
        except:
            start_id = 1


antronio = Xenforo(url="http://www.antronio.cl/")

print "[INFO] Intentando ingresar al foro."
antronio.login(user="USER", password="PASSWORD")

print "[INFO] Obteniendo el ultimo post."
last_id = antronio.get_last_post_id()

print "[INFO] Comenzaremos a dar likes :D"

for i in range(start_id, last_id):
    # Recargar token cada 10 peticiones
    if i % 10 == 0:
        antronio.get_token()

    res = antronio.like(i, True, "Abushear")
    if res is True:
        print "Like al post ID: {0}".format(i)
    else:
        print "No se pudo dar like al post ID: {0}".format(i)

    # Guardar el ultimo ID procesado
    f = open(SAVE_FILE, "w")
    f.write(json.dumps({'id': i}))
    f.close()


