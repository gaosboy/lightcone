from urllib.parse import urlparse, urlencode, parse_qs

from gramai.utils import is_str


class URL(str):
    def __new__(cls, url=None, scheme=None, host=None, port=None, path=None, fragment=None):
        obj = super().__new__(cls, url)
        _parsed = urlparse(url)
        obj._scheme = scheme if is_str(scheme) else _parsed.scheme
        obj._host = host if is_str(host) else _parsed.hostname
        obj._port = port if port is not None else _parsed.port
        obj._path = path if is_str(path) else _parsed.path
        obj._fragment = fragment if is_str(fragment) else _parsed.fragment

        return obj

    def __init__(self, url=None, scheme=None, host=None, port=None, path=None, fragment=None):
        super().__init__()
        _parsed = urlparse(url)
        self._scheme = scheme if is_str(scheme) else _parsed.scheme
        self._host = host if is_str(host) else _parsed.hostname
        self._port = port if port is not None else _parsed.port
        self._path = path if is_str(path) else _parsed.path
        self._fragment = fragment if is_str(fragment) else _parsed.fragment
        self._query = _parsed.query if _parsed is not None else ""
        self._query_dict = self._parse_query_to_dict(self._query)

    def __str__(self):
        return self._unparse_url()

    def __repr__(self):
        return self._unparse_url()

    def set_param(self, key, value):
        if key is not None:
            if value is not None:
                self._query_dict[key] = value
            elif key in self.query_dict:
                self._query_dict.pop(key)
        self._query = urlencode(self.query_dict)
        return self

    def get_param(self, key) -> str:
        return self.query_dict.get(key, None)

    @property
    def query_dict(self) -> dict:
        return self._query_dict or {}

    @query_dict.setter
    def query_dict(self, value):
        _ = value
        AttributeError("不允许设置属性")

    @property
    def scheme(self) -> str:
        return self._scheme

    @scheme.setter
    def scheme(self, value):
        self._scheme = value

    @property
    def host(self) -> str:
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self) -> str:
        return "80" if self._port is None else self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def path(self) -> str:
        return f"/{self._path.strip('/').rstrip('/')}"

    @path.setter
    def path(self, value):
        _path = value.rstrip("/").strip("/")
        self._path = f"/{value}"

    @property
    def query(self) -> str:
        return urlencode(self.query_dict)

    @query.setter
    def query(self, value):
        raise AttributeError("使用 url.set_param(key, value)设置参数")

    @property
    def fragment(self) -> str:
        return self._fragment

    @fragment.setter
    def fragment(self, value):
        self._fragment = value

    @staticmethod
    def _parse_query_to_dict(query):
        parsed_query = parse_qs(query)
        return {k: v[0] if len(v) == 1 else v for k, v in parsed_query.items()}

    def _unparse_url(self):
        _parsed = ""
        if is_str(self._scheme, False):
            _parsed += self._scheme
        if is_str(self._host, False):
            _parsed += f"://{self._host}"
        if is_str(self._port, False):
            _parsed += f":{str(self._port)}"
        if is_str(self._path, False):
            _parsed += f"/{self._path.strip('/').rstrip('/')}"
        if is_str(self.query, False):
            _parsed += f"?{self.query}"
        if is_str(self._fragment, False):
            _parsed += f"#{self._fragment}"
        return _parsed
