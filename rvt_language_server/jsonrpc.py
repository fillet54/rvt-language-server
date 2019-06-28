# Simple JSONRPC implementation
# IN WORK DUE TO FUTURES ARE A PAIN
import sys
import logging
import codecs
from Queue import Queue
from threading import Thread

log = logging.getLogger(__name__)

# When migrating to python 3 upgrade to use futures to implement
# thread pool


class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class ThreadPool:
    """ Pool of threads consuming tasks from a queue """

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()

#    CODE = -32700
#    MESSAGE = 'Parse Error'
#
#    CODE = -32600
#    MESSAGE = 'Invalid Request'
#
#    CODE = -32601
#    MESSAGE = 'Method Not Found'
#
#    CODE = -32602
#    MESSAGE = 'Invalid Params'
#
#
#    CODE = -32602
#    MESSAGE = 'Internal Error'
#
#    CODE = -32800
#    MESSAGE = 'Request Cancelled'


def _version_mismatch(msg):
    try:
        return not ('jsonrpc' in msg and msg['jsonrpc'] == '2.0')
    except:
        return True


def _is_notification(msg):
    return 'id' not in msg and 'method' in msg


def _is_response(msg):
    return 'id' in msg and 'method' not in msg and ('result' in msg or 'error' in msg)


def _is_request(msg):
    return 'id' in msg and 'method' in msg and not _is_response(msg)


class JsonRpcServer(object):
    JSONRPC_VERSION = '2.0'

    def __init__(self, handler_resolver, write_fn):
        # resolves a handler function based on method name or returns none
        self.resolver = handler_resolver

        # function to write server to client messages
        self.write = write_fn

        self.executor = ThreadPool(10)
        self.async_jobs = {}

    def on_message(self, msg):
        'Processes a single JsonRPC message'

        if _version_mismatch(msg):
            log.warn("Unknown message %s", msg)
            return
        if _is_request(msg):
            self._handle_request(
                msg['id'], msg['method'], msg.get('params', {}))
        elif _is_response(msg):
            pass
        elif _is_notification(msg):
            self._handle_notification(msg['method'], msg.get('params', {}))

    def _dispath_and_handle(self, method, params):
        'Resolves handler and executes handler for messages'
        try:
            handler = self.resolver(method)
        except:
            log.warn("Error resolving handler for %s" % method)

        if handler is None:
            log.debug("Ignoring notification for %s" % method)
            return

        try:
            result = handler(params)
            return result
        except:
            log.warn("Error handling notification for %s" % method)
            return

        return

    def _handle_notification(self, method, params):
        result = self._dispath_and_handle(method, params)

        if callable(result):
            # Execute async on executor
            self.executor.add_task(result)

    def _handle_request(self, id, method, params):
        result = self._dispath_and_handle(method, params)

        if callable(result):
            pass

    def _request_finished_callback(self, id):
        def callback(result):
            pass


class StreamingConnection(object):
    'Reads and Writes to streams converting to/from json'

    def __init__(self, writer, reader):
        self.writer = writer
        self.reader = reader

    def _read_headers(self):
        reader = codecs.getreader('ascii')(self.reader)
        headers = {}
        line = self.reader.readline()
        while line and line.strip():
            if ':' not in line:
                log.error('Header expected instead got "%s"' % line)
                return None
            key, val = line.split(':', 1)
            headers[key.strip()] = val.strip()
            line = self.reader.readline()

        # EOF
        if not line:
            return None

        return headers

    CODEC_REPLACEMENTS = {'utf8': 'utf-8'}

    def _read_message(self):
        headers = self._read_headers()
        content_length = headers.get('Content-Length', None)
        if content_length is None:
            return None

        content_type = headers.get('Content-Type', 'utf-8')
        # handle codec replacements (i.e JSONRPC 1.0)
        content_type = self.CODEC_REPLACEMENTS.get(content_type, content_type)
        try:
            reader = codecs.getreader(content_type)(self.reader)
        except:
            log.warn("Invalid Content-Type: %s" % (content_type))
            reader = self.reader

        return reader.read(int(content_length))

# run
# for msg in StreamingConnection
