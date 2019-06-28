import os
dir_path = os.path.dirname(os.path.realpath(__file__))
activate_this = os.path.join(
    dir_path, '..', '.venv', 'Scripts', 'activate_this.py')
exec(open(activate_this).read(), {'__file__': activate_this})

import json
import logging
import signal
import sys

from tornado import web, ioloop, websocket

from handler import LanguageServerStreamHandler

# logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Application(web.Application):
    is_closing = False

    def signal_handler(self, signum, frame):
        log.info('exiting...')
        self.is_closing = True

    def try_exit(self):
        if self.is_closing:
            ioloop.IOLoop.current().stop()
            log.info('exit success')


# app = Application([
#    (r"/python", LanguageServerWebSocketHandler)
# ])
# app.listen(3000, address='127.0.0.1')
# signal.signal(signal.SIGINT, app.signal_handler)
# ioloop.PeriodicCallback(app.try_exit, 100).start()
#
# log.info("starting language server")
# ioloop.IOLoop.current().start()
#
__DEBUG = True

if __DEBUG:
    from_client = open('c:/temp/from-client.txt', 'w')
    to_client = open('c:/temp/to-client.txt', 'w')


def MessageGenerator(stream):
    '''Takes a stream of language server protocol jsonrpc and yields complete
       messages based on 'Content-Length' header'''

    msg_len = None
    while True:
        line = stream.readline()
        if not line:
            return

        line = line.strip('\n')

        # Header
        if ':' in line:
            key, val = line.split(':', 1)
            if key.strip().lower() == 'content-length':
                msg_len = int(val.strip())

                if __DEBUG:
                    from_client.write(line + '\n')
            # Ignore any other headers. I don't even know if any get sent.

        # Body
        elif line == '' and msg_len is not None:
            msg = ''
            remaining = msg_len
            while remaining > 0:
                to_read = min(1024, remaining)
                remaining -= to_read
                data = stream.read(to_read)
                if not data:
                    return

                if __DEBUG:
                    from_client.write(data)

                msg += data
            yield msg
            msg_len = None  # clear active message
        else:
            # Throw away stream out of sync
            pass


def write_message(message):
    if __DEBUG:
        to_client.write(
            'Content-Length: {0}\n\n{1}'.format(len(message), message))
    sys.stdout.write(
        'Content-Length: {0}\n\n{1}'.format(len(message), message))
    sys.stdout.flush()


handler = LanguageServerStreamHandler(write_message)

for msg in MessageGenerator(sys.stdin):
    handler.on_message(msg)
