from src.httpd import Headers, HttpCodes


class TestHttpCodes:
    def test_resolve_code_message(self):
        assert HttpCodes.get_message(200) == 'OK'
        assert HttpCodes.get_message(404) == 'Not Found'
        assert HttpCodes.get_message(414) == 'Request-URI Too Large'
        assert HttpCodes.get_message(700) == 'Unknown Status Code'


class TestHeaders:
    def test_to_bytes(self):
        headers = Headers()
        headers.set('Bla-Bla', '123')
        headers.set('Hi', 'there')

        assert str(headers) == 'Bla-Bla: 123\r\nHi: there'
