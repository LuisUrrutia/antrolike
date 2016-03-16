# coding=utf-8
import validators
import requests
from bs4 import BeautifulSoup
import re
from classes.Forum import Forum
import json

class URLError(Exception):
    def __bool__(self):
        return False


class LoginError(Exception):
    def __bool__(self):
        return False


class GeneralError(Exception):
    def __bool__(self):
        return False


class Xenforo(object):

    base_url = None
    title = None

    __session = None
    __token = None

    def __init__(self, url):
        # Comprobar si la URL es valida
        if not validators.url(url):
            raise URLError("La url provista no es valida.")

        s = self.__session = requests.Session()
        # Petición GET a URL
        req = s.get(url)
        # Comprobar si es posible conectarse directamente a la URL
        if req.status_code != 200:
            raise URLError("No es posible conectarse directamente con la url.")

        # HTML de la página web
        body = req.text
        # Parsear HTML
        soup = BeautifulSoup(body, 'html.parser')

        self.title = soup.title.string
        self.base_url = url.rstrip('/')

    def login(self, email=None, user=None, password=None):
        user_email = None
        if email is None and user is None:
            raise LoginError("Debes ingresar un usuario o correo electrónico.")

        if email is None:
            user_email = user
        elif validators.email(email):
            user_email = email
        else:
            raise LoginError("El correo electrónico no es valido.")

        if password is None:
            raise LoginError("Debes ingresar una contraseña.")

        s = self.__session

        data = {
            'login': user_email,
            'password': password,
            'register': 0,
            'cookie_check': 1,
            '_xfToken': '',
            'redirect': self.base_url
        }
        req = s.post("{0}/login/login".format(self.base_url), data=data)
        if req.status_code != 200 or req.url != self.base_url:
            raise LoginError("No se pudo ingresar al sitio, comprueba las credenciales.")

    def get_forums(self):
        s = self.__session
        req = s.get("{0}/misc/quick-navigation-menu".format(self.base_url))
        if req.status_code != 200:
            raise GeneralError("No podemos conectarnos al foro")
        soup = BeautifulSoup(req.text, 'html.parser')
        links = soup.find_all('a')

        forum_link = re.compile("^forums/[^(/-/|/#)]+/$")
        all_links = []
        forum_objects = []
        for link in links:
            l = link.get('href')
            if l is not None and forum_link.match(l) and l not in all_links:
                name = link.find("span").string
                f = Forum(name=name, url="{0}/{1}".format(self.base_url, l))
                forum_objects.append(f)
            all_links.append(l)
        return forum_objects

    def get_token(self):
        s = self.__session
        req = s.get(self.base_url)
        if req.status_code != 200:
            raise GeneralError("No se puede conectar a la página.")
        soup = BeautifulSoup(req.text, 'html.parser')
        try:
            token = soup.find("input", {"name": "_xfToken"})['value']
            self.__token = token
            return token
        except:
            return None

    def get_last_post_id(self):
        s = self.__session
        req = s.get("{0}/recent-activity/".format(self.base_url))
        if req.status_code != 200:
            raise GeneralError("No se puede conectar a la página.")

        soup = BeautifulSoup(req.text, 'html.parser')
        links = soup.find_all("a")

        post_link = re.compile("^posts/\d+/$")
        for link in links:
            if post_link.match(link.get('href')):
                link = link.get('href').rstrip("/")
                id = link.replace("posts/", "")
                try:
                    id = int(id)
                    return id
                except:
                    pass

    def like(self, id, ensure=False, msg_to_identify=None):
        if ensure is True and msg_to_identify is None:
            raise GeneralError("Debes especificar un texto a comprobar para saber si ya diste like.")

        s = self.__session
        token = self.__token

        if token is None and ensure is False:
            token = self.get_token()

        with_like = False
        if ensure is True:
            req = s.get("{0}/posts/{1}/like".format(self.base_url, id))
            with_like = msg_to_identify in req.text
            soup = BeautifulSoup(req.text, 'html.parser')
            try:
                token = soup.find("input", {"name": "_xfToken"})['value']
                self.__token = token
            except:
                token = self.get_token()

        if with_like is True:
            return True

        if token is None:
            raise GeneralError("No se pudo obtener el token")

        data = {
            '_xfRequestUri': self.base_url,
            '_xfNoRedirect': 1,
            '_xfToken': token,
            '_xfResponseType': 'json'
        }
        req = s.post("{0}/posts/{1}/like".format(self.base_url, id), data=data)
        if req.status_code != 200:
            return False
        res = json.loads(req.text)

        if 'error' in res:
            return False

        if 'cssClasses' in res:
            like = res['cssClasses']['like']
            if like == '-':
                return True
            else:
                return self.like(id)
        else:
            return False

