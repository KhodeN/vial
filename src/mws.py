from .httpd import HttpCodes, HttpDaemon
from .isomorp_utils import path_join
from .mime_types import MimeTypes


class MicroWebServer(HttpDaemon):

    def __init__(self):
        super().__init__()
        self._routes = dict()

    def handle_request(self, req, res):
        print(req.path)

        for route, handlers in self._routes.items():
            if req.path == route:
                for handler in handlers:
                    handler(req, res)
                return

        res.send_error(HttpCodes.NotFound)

    def add_route(self, route, handler):
        if route not in self._routes:
            self._routes[route] = []

        self._routes[route].append(handler)

    def add_file_routes(self, static_dir, static_files):
        for f in static_files:
            def send_file(req, res, path=path_join(static_dir, f)):
                res.send_file(path, MimeTypes.get_for_file(path))

            self.add_route('/{}'.format(f), send_file)

    def get_routes(self):
        return self._routes.keys()
