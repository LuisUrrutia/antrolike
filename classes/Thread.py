class Thread(object):
    id = 0
    name = None
    url = None

    def __init__(self, id, name, url):
        self.id = id
        self.name = name
        self.url = url
