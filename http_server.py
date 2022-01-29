#!/usr/bin/env python3

import os, sys
import json
import subprocess
from functools import partial
from http.server import SimpleHTTPRequestHandler, BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs
from html.parser import HTMLParser


class CommandException(Exception):

    """Failed to execute the command
    """

    def __init__(self, error_code, error_str):
        self.code = error_code
        self.err_str = error_str


class MatchedHTMLParser(HTMLParser):

    def __init__(self, words, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lasttag = ''
        self.title = ''
        self.desc = ''
        self.search_words = words

    def handle_starttag(self, tag, _):
        self.lasttag = tag

    def handle_data(self, data):
        if self.lasttag == 'title':
            self.title = data
        elif self.lasttag == 'body':
            self.desc = data

    def get_meta(self):
        return (self.title, self.desc)


class SearchableHttpServer(SimpleHTTPRequestHandler):

    """HTTP searver which can search on local system.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # We only need to custom the GET request.
    def do_GET(self):
        """Serve a GET request.
        """
        query = urlparse(self.path).query
        if not query:
            return super().do_GET()

        params = parse_qs(query)
        search_dir = params['dir']
        search_words = params['word']

        try:
            candidates = self.search_candidates(
                    search_dir[0] if search_dir else '.',
                    search_words)
        except CommandException as e:
            print('** Search failed, return {}, message:\n{}'.format(
                    e.code, e.err_str))
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')
            return None
        except Exception as e:
            print('** Search failed, message:\n{}'.format(e))
            self.send_error(HTTPStatus.NOT_FOUND, str(e))
            return None

        res = []
        for file in candidates:
            # parse the html to get title and the short description
            html_parser = MatchedHTMLParser(search_words)
            with open(file) as f:
                content = f.read()
            html_parser.feed(content)
            res.append(html_parser.get_meta())
        json_str = self.assemble_json(res)
        self.wfile.write(json_str.encode())

    def assemble_json(self, res):
        """Remove empty item and convert to json format
        """
        ret = {}
        for title, desc in res:
            if title and desc:
                res[title] = desc
        return json.dumps(ret)

    def search_candidates(self, d, words):
        """Search @words in @d, and return the short desc for match file.
        """
        search_dir = os.path.abspath(os.path.join(self.directory, d))
        if os.path.commonpath([self.directory]) != \
           os.path.commonpath([self.directory, search_dir]):
            # For safty, we need to check the search directory is not
            # "overflow"
            raise Exception('Invalid Directory: {}'.format(d))

        try:
            output = subprocess.check_output(
                    ['grep', '-ilnrw'] + words + [search_dir])
        except subprocess.CalledProcessError as e:
            raise CommandException(e.output, e.returncode)
        filelist = output.decode('utf-8').strip().split('\n')
        return filelist


def test(HandlerClass=BaseHTTPRequestHandler,
         ServerClass=ThreadingHTTPServer,
         protocol="HTTP/1.0", port=8000, bind=""):
    """Test the HTTP request handler class.

    This runs an HTTP server on port 8000 (or the port argument).
    """
    server_address = (bind, port)

    HandlerClass.protocol_version = protocol
    with ServerClass(server_address, HandlerClass) as httpd:
        sa = httpd.socket.getsockname()
        serve_message = ("Serving HTTP on {host} port {port} "
                        "(http://{host}:{port}/) ...")
        print(serve_message.format(host=sa[0], port=sa[1]))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            sys.exit(0)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('port', action='store',
                        default=8000, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8000]')
    parser.add_argument('--directory', '-d', default=os.getcwd(),
                        help='Specify alternative directory '
                        '[default:current directory]')
    parser.add_argument('--bind', '-b', default='', metavar='ADDRESS',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')
    args = parser.parse_args()
    handler_class = partial(SearchableHttpServer, directory=args.directory)
    test(HandlerClass=handler_class, port=args.port, bind=args.bind)
