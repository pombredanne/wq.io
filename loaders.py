from __future__ import print_function
import requests
try:
    # Python 3
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO
from wq.io.version import VERSION
from .exceptions import LoadFailed


class BaseLoader(object):
    def load(self):
        raise NotImplementedError


class FileLoader(BaseLoader):
    filename = None
    no_pickle_loader = ['file']

    def load(self):
        try:
            self.file = open(self.filename)
        except:
            self.file = StringIO()

    def save(self):
        file = open(self.filename, 'w+')
        self.dump(file)
        file.close()
        self.load()


class BinaryFileLoader(FileLoader):
    def load(self):
        self.file = open(self.filename, 'rb')


class StringLoader(BaseLoader):
    string = ""

    def load(self):
        self.file = StringIO(self.string)

    def save(self):
        file = StringIO()
        self.dump(file)
        self.string = file.getvalue()
        file.close()
        self.load()


class NetLoader(BaseLoader):
    "NetLoader: opens HTTP/REST resources for use in wq.io"

    username = None
    password = None
    debug = False

    @property
    def url(self):
        raise NotImplementedError

    @property
    def user_agent(self):
        return "wq.io/%s (%s)" % (VERSION, requests.utils.default_user_agent())

    @property
    def headers(self):
        return {
            'User-Agent': self.user_agent,
        }

    def load(self, **kwargs):
        self.file = StringIO(self.GET())

    def req(self, url=None, method=None, params=None, body=None, headers={}):
        if url is None:
            url = self.url

        if params is None:
            params = getattr(self, 'params', None)

        if isinstance(params, str):
            url += '?' + params
            params = None

        if self.debug:
            print("%s: %s" % (method, url))

        if self.username is not None and self.password is not None:
            auth = (self.username, self.password)
        else:
            auth = None

        all_headers = self.headers.copy()
        all_headers.update(headers)

        resp = requests.request(
            method, url,
            params=params,
            headers=all_headers,
            auth=auth,
            data=body,
        )

        if resp.status_code < 200 or resp.status_code > 299:
            raise LoadFailed(
                resp.text,
                path=url,
                code=resp.status_code,
            )

        return resp.text

    def GET(self, **kwargs):
        return self.req(method='GET', **kwargs)

    def POST(self, **kwargs):
        return self.req(method='POST', **kwargs)

    def PUT(self, **kwargs):
        return self.req(method='PUT', **kwargs)

    def DELETE(self, **kwargs):
        return self.req(method='DELETE', **kwargs)
