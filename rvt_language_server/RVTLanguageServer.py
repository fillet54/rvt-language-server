import logging

from pyls_jsonrpc import dispatchers, endpoint

log = logging.getLogger(__name__)


class RVTLanguageServer(dispatchers.MethodDispatcher):
    """Implement a JSON RPC method dispatcher for the language server protocol."""

    def __init__(self):
        # Endpoint is lazily set after construction
        self.endpoint = None

    # { "openClose": True, }

    def m_initialize(self, rootUri=None, **kwargs):
        #log.info("Got initialize params: %s", kwargs)
        return {"capabilities": {
            "textDocumentSync": {
                "openClose": True
            },
        }}

    def m_text_document__did_open(self, textDocument=None, **_kwargs):
        #log.info("Opened text document %s", textDocument)
        self.endpoint.notify('textDocument/publishDiagnostics', {
            'uri': textDocument['uri'],
            'diagnostics': [{
                'range': {
                    'start': {'line': 0, 'character': 0},
                    'end': {'line': 1, 'character': 0},
                },
                'message': 'Some very bad Python code',
                'severity': 1  # DiagnosticSeverity.Error
            }]
        })

    def m_shutdown(self, rootUri=None, **kwargs):
        return None
