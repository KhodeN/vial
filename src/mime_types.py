class MimeTypes:
    __cache = dict()

    Css = ('text/css', {'css'})
    Html = ('text/html', {'html', 'htm'})
    JavaScript = ('application/javascript', {'js', 'mjs'})
    Text = ('text/plain', {'txt'})
    Png = ('image/png', {'png'})

    @classmethod
    def get_for_ext(cls, ext):
        if ext not in cls.__cache:
            cls.__cache[ext] = None
            for v in cls.__dict__.values():
                if isinstance(v, tuple) and ext in v[1]:
                    cls.__cache[ext] = v[0]

        return cls.__cache[ext]

    @classmethod
    def get_for_file(cls, filename):
        ext = filename.rsplit('.', 1)[-1]

        return cls.get_for_ext(ext)

    @classmethod
    def get_mime(cls, mime_type):
        if isinstance(mime_type, tuple):
            return mime_type[0]

        return mime_type
