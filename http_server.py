#!/usr/bin/env python3

import os
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class SearchableHttpServer(SimpleHTTPRequestHandler):

    """HTTP searver which can search on local system.
    """

    # We only need to custom the GET request.
    def do_GET(self):
        if not self.path.endswith('.html'):
            params = parse_qs(urlparse(self.path).query)
            search_dir = params['dir']
            search_words = params['words']
            return self.search(search_dir, search_words)
        return super().do_GET()

    def search(self, d, words):
        """Search @words in @d, and return the short desc for match file.

        TODO:
            1. we need to parse the matched html, to get the title.
            2. and get the short description of content
        """
        command = 'grep -ilnrw {} {}'.format(words, d)
        return os.system(command)
