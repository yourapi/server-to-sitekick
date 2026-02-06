#!/usr/bin/env python3
"""Simple HTTP server that echoes incoming API calls."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class EchoHandler(BaseHTTPRequestHandler):
    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _send_response(self, body, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        body = self._read_body()
        body_text = body.decode('utf-8', errors='replace')
        if body_text:
            try:
                parsed = json.loads(body_text)
                print(json.dumps(parsed, indent=2, sort_keys=True))
            except json.JSONDecodeError:
                pass
        # Build a simple JSON response with headers and body as strings.
        response = "{\"method\": \"%s\", \"path\": \"%s\", \"headers\": %s, \"body\": %s}" % (
            self.command,
            self.path,
            repr(dict(self.headers)),
            repr(body_text),
        )
        self._send_response(response.encode("utf-8"))

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_PATCH(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def log_message(self, format, *args):
        # Keep logs concise in console.
        print("%s - - %s" % (self.address_string(), format % args))


def main():
    host = "0.0.0.0"
    port = 8000
    server = HTTPServer((host, port), EchoHandler)
    print("Echo server listening on http://%s:%s" % (host, port))
    server.serve_forever()


if __name__ == "__main__":
    main()
