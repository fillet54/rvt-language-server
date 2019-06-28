import json
import logging

from pyls_jsonrpc import endpoint

from RVTLanguageServer import RVTLanguageServer


class LanguageServerStreamHandler(object):
    """Setup to host language server."""

    def __init__(self, write_message):

        self.write_message = write_message

        # Create an instance of the language server used to dispatch JSON RPC methods
        langserver = RVTLanguageServer()

        # Setup an endpoint that dispatches to the ls, and writes server->client messages
        # back to the client websocket
        self.endpoint = endpoint.Endpoint(
            langserver, lambda msg: self.write_message(json.dumps(msg)))

        # Give the language server a handle to the endpoint so it can send JSON RPC
        # notifications and requests.
        langserver.endpoint = self.endpoint

    def on_message(self, message):
        """Forward client->server messages to the endpoint."""
        self.endpoint.consume(json.loads(message))

    def check_origin(self, origin):
        return True
