import socket

from .isomorp_utils import file_size, is_micropython


HTTP_VERSION = 'HTTP/1.1'
HEADERS_END = b'\r\n\r\n'
HEADER_SEP = b'\r\n'
HEADER_VALUE_SEP = b': '
BUFFER_SIZE = 2 ** 12  # 4kB

if is_micropython():
    FILE_BUFFER_SIZE = 2 ** 123  # 4kB
else:
    FILE_BUFFER_SIZE = 2 ** 20  # 1MB


class HttpHeaders:
    ContentLength = "Content-Length"
    ContentType = "Content-Type"
    Host = "Host"


class HttpMethods:
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"


class HttpCodes:
    Continue = (100, "Continue")
    SwitchingProtocols = (101, "Switching Protocols")
    OK = (200, "OK")
    Created = (201, "Created")
    Accepted = (202, "Accepted")
    NonAuthoritativeInformation = (203, "Non-Authoritative Information")
    NoContent = (204, "No Content")
    ResetContent = (205, "Reset Content")
    PartialContent = (206, "Partial Content")
    MultipleChoices = (300, "Multiple Choices")
    MovedPermanently = (301, "Moved Permanently")
    MovedTemporarily = (302, "Moved Temporarily")
    SeeOther = (303, "See Other")
    NotModified = (304, "Not Modified")
    UseProxy = (305, "Use Proxy")
    BadRequest = (400, "Bad Request")
    Unauthorized = (401, "Unauthorized")
    PaymentRequired = (402, "Payment Required")
    Forbidden = (403, "Forbidden")
    NotFound = (404, "Not Found")
    MethodNotAllowed = (405, "Method Not Allowed")
    NotAcceptable = (406, "Not Acceptable")
    ProxyAuthenticationRequired = (407, "Proxy Authentication Required")
    RequestTimeout = (408, "Request Time-out")
    Conflict = (409, "Conflict")
    Gone = (410, "Gone")
    LengthRequired = (411, "Length Required")
    PreconditionFailed = (412, "Precondition Failed")
    RequestEntityTooLarge = (413, "Request Entity Too Large")
    RequestUriTooLarge = (414, "Request-URI Too Large")
    UnsupportedMediaType = (415, "Unsupported Media Type")
    InternalServerError = (500, "Internal Server Error")
    NotImplemented = (501, "Not Implemented")
    BadGateway = (502, "Bad Gateway")
    ServiceUnavailable = (503, "Service Unavailable")
    GatewayTimeout = (504, "Gateway Time-out")
    HttpVersionNotSupported = (505, "HTTP Version not supported")

    @classmethod
    def get_message(cls, code):
        # type: (int) -> str
        for k, v in cls.__dict__.items():
            if isinstance(v, tuple) and v[0] == code:
                return v[1]

        return 'Unknown Status Code'


class Headers:
    def __init__(self):
        self._headers = dict()  # type: dict[HttpHeaders, str]

    def set(self, name, value):
        # type: (str, str) -> None
        if value is not None:
            self._headers[name] = value
            return

        # remove if None
        if name in self._headers:
            del self._headers

    def get(self, name):
        # type: (str) -> str
        return self._headers.get(name, None)

    def get_all(self):
        # type: () -> dict[str, str]
        return self._headers.copy()

    def __repr__(self):
        return repr(self._headers)

    def __str__(self):
        sep = HEADER_VALUE_SEP.decode()
        lines = ['{}{}{}'.format(k, sep, v) for k, v in self._headers.items()]

        return HEADER_SEP.decode().join(lines)

    def to_bytes(self):
        return str(self).encode() + HEADERS_END

    @classmethod
    def from_bytes(cls, headers_raw):
        # type: (bytes) -> Headers
        headers = cls()
        for line in headers_raw.split(HEADER_SEP):
            if not line:
                continue
            header_name, _, value = line.partition(HEADER_VALUE_SEP)
            headers.set(header_name.decode(), value.decode())

        return headers

    @classmethod
    def from_dict(cls, d):
        headers = cls()
        for k, v in d.items():
            headers.set(k, v)

        return headers


class HttpRequest:
    def __init__(self, client_address, start_line, headers, body):
        # type: (tuple[str, int], str, Headers, bytes) -> None

        self.client_address = client_address
        self.method, self.path, self.protocol = self.parse_start_line(start_line)
        self.headers = headers
        self.body = body

    def parse_start_line(self, start_line):
        # type: (str) -> tuple[str, str, str]
        method, path, protocol = start_line.split(' ', maxsplit=2)

        return method, path, protocol

    @property
    def url(self):
        return "http://{}/{}".format(self.headers.get(HttpHeaders.Host), self.path)

    def __repr__(self):
        return self.path


class HttpResponse:
    def __init__(self, connection):
        # type: (socket.socket) -> None
        self.connection = connection

    def get_start_line(self, code):
        # type: (int) -> bytes

        return '{protocol} {code} {message}'.format(
            protocol=HTTP_VERSION,
            code=code,
            message=HttpCodes.get_message(code)
        ).encode() + HEADER_SEP

    def send(self, code, headers, body=None):
        self.connection.sendall(self.get_start_line(code))

        if body:
            if not isinstance(body, bytes):
                body = body.encode()
            headers.set(HttpHeaders.ContentLength, str(len(body)))

        self.connection.sendall(headers.to_bytes())

        if body:
            self.connection.sendall(body)

    def send_file(self, path, content_type):
        try:
            headers = Headers()
            headers.set(HttpHeaders.ContentType, content_type)
            headers.set(HttpHeaders.ContentLength, str(file_size(path)))

            with open(path, 'rb') as f:

                self.connection.sendall(self.get_start_line(200))
                self.connection.sendall(headers.to_bytes())

                while True:
                    data = f.read(FILE_BUFFER_SIZE)
                    if not data:
                        break
                    self.connection.sendall(data)

        except OSError as e:
            print(e)
            self.send_error(HttpCodes.NotFound)

    def send_error(self, code):
        headers = Headers()
        headers.set(HttpHeaders.ContentType, 'text/plain')

        code = code[0] if isinstance(code, tuple) else code

        return self.send(code, headers)

    def send_unsupported_error(self):
        code, _ = HttpCodes.HttpVersionNotSupported

        return self.send_error(code)


class HttpDaemon:

    def __init__(self, ):
        self.__socket = socket.socket()
        self.request_handler = None

    def start(self, host='0.0.0.0', port=80):
        s = self.__socket

        s.bind((host, port))
        s.listen()

        print("Server started on http://{}:{}".format(host, port))
        print("Press Ctrl+C to abort.")

        client_socket = None
        while True:
            if self.__socket is None:
                break
            try:
                client_socket, client_address = s.accept()

                req = self.read_request(client_socket, client_address)
                resp = HttpResponse(client_socket)

                if req is None:
                    resp.send_error(HttpCodes.BadRequest)
                    continue

                if req.protocol != HTTP_VERSION:
                    resp.send_unsupported_error()
                    continue

                self.handle_request(req, resp)

            except KeyboardInterrupt:
                self.stop()
                print("Goodbye!")
                return

            except Exception as e:
                print(e)
                raise e

            finally:
                if client_socket:
                    client_socket.close()

    def stop(self):
        if self.__socket is not None:
            self.__socket.close()
            self.__socket = None

    def read_request(self, connection, address):
        # type: (socket.socket, tuple[str, int]) -> HttpRequest | None

        buffer = []

        data = connection.recv(BUFFER_SIZE)
        if not data:
            return None
        buffer.append(data)
        received_data = b''.join(buffer)

        if HEADERS_END not in received_data:
            return None

        start_line, _, headers_and_body = received_data.partition(HEADER_SEP)
        headers_raw, _, body = headers_and_body.partition(HEADERS_END)
        headers = self.parse_headers(headers_raw)

        content_length = headers.get(HttpHeaders.ContentLength)
        if content_length:
            total_length = len(body)
            while total_length < int(content_length):
                data = connection.recv(BUFFER_SIZE)
                if not data:
                    break
                buffer.append(data)
                total_length += len(data)
            received_data = b''.join(buffer)

        # TODO handle huge headers (more then BUFFER_SIZE)

        _, _, body = received_data.partition(HEADERS_END)

        return HttpRequest(address, start_line.decode(), headers, body)

    def parse_headers(self, headers_raw):
        # type: (bytes) -> Headers
        return Headers.from_bytes(headers_raw)

    def handle_request(self, req, res):
        # type: (HttpRequest, HttpResponse) -> None
        print('Raw request\n---\n', req, '\n---')
        print('res', res)
