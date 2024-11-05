import os

from src.httpd import Headers, HttpCodes, HttpHeaders, HttpRequest, HttpResponse
from src.mime_types import MimeTypes
from src.mws import MicroWebServer


STATIC_DIR = 'demo_static'


def run():
    server = MicroWebServer()

    def handle_index(req, res):
        res.send_file(
            path=STATIC_DIR + os.sep + 'index.html',
            content_type=MimeTypes.get_mime(MimeTypes.Html)
        )

    server.add_route('/', handle_index)

    server.add_file_routes(
        static_dir=STATIC_DIR,
        static_files=[
            'app.js',
            'index.html',
            'logo.png',
            'style.css',
        ])

    def handle_routes(req, res):
        # type: (HttpRequest, HttpResponse) -> None

        body = '\n'.join(server.get_routes())

        res.send(HttpCodes.OK, Headers.from_dict({
            HttpHeaders.ContentType: MimeTypes.get_mime(MimeTypes.Text)
        }), body)

    server.add_route('/routes', handle_routes)
    try:
        server.start(host='0.0.0.0', port=80)
    finally:
        server.stop()


if __name__ == '__main__':
    run()
