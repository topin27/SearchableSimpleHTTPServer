#!/usr/bin/env python3

import os, sys
import json
import subprocess
from functools import partial
from http.server import SimpleHTTPRequestHandler
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
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

    def handle_endtag(self, _):
        self.lasttag = ''

    def handle_data(self, data):
        if not self.lasttag:
            return
        if self.lasttag == 'title':
            self.title = data.strip('\n')
        elif self.lasttag == 'body':
            print('data:', data)
            self.desc = data.replace('\n', ' ').strip()
            print(self.desc)
        else:
            pass

    def get_meta(self):
        return [self.title, self.desc]


class SearchableHttpServer(SimpleHTTPRequestHandler):

    """HTTP searver which can search on local system.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send_cors_headers(self):
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        self.send_header('Access-Control-Allow-Headers',
                         'Authorization, Content-Type')

    # We only need to custom the GET request.
    def do_GET(self):
        """Serve a GET request.
        """
        parse_res = urlparse(self.path)
        if parse_res.path != '/search' or not parse_res.query:
            return super().do_GET()

        params = parse_qs(parse_res.query)
        search_dir = params['dir']
        search_words = params['word']

        try:
            candidates = self.search_candidates(
                    search_dir[0] if search_dir else '.',
                    search_words)
        except CommandException as e:
            if e.code == 1:
                self.wfile.write('{}'.encode())
                return None
            print('** Search failed, return {}, message:\n{}'.format(
                  e.code, e.err_str))
            return None

        res = []
        for file in candidates:
            # parse the html to get title and the short description
            html_parser = MatchedHTMLParser(search_words)
            with open(file) as f:
                content = f.read()
            html_parser.feed(content)
            meta = html_parser.get_meta()
            meta.append(os.path.relpath(file, self.directory))
            res.append(meta)
        json_str = self.assemble_json(res)
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json_str.encode())

    def assemble_json(self, res):
        """Remove empty item and convert to json format
        """
        ret = []
        for title, desc, file in res:
            if title and desc:
                ret.append({'title': title, 'desc': desc, 'file': file})
        return json.dumps(ret)

    def search_candidates(self, d, words):
        """Search @words in @d, and return the short desc for match file.
        """
        search_dir = os.path.abspath(os.path.join(self.directory, d))
        if os.path.commonpath([self.directory]) != \
           os.path.commonpath([self.directory, search_dir]):
            # For safty, we need to check the search directory is not "overflow"
            raise Exception('Invalid Directory: {}'.format(d))

        try:
            cmd = ['grep', '-ilnRw', '--include=*.html'] + words + [search_dir]
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            raise CommandException(e.returncode, e.output)
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
