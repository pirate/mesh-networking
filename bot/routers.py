def chunk(iterable, chunk_size=20):
    """chunk an iterable [1,2,3,4,5,6,7,8] -> ([1,2,3], [4,5,6], [7,8])"""
    items = []
    for value in iterable:
        items.append(value)
        if len(items) == chunk_size:
            yield items
            items = []
    if items:
        yield items


class MessageRouter(object):
    node = None
    routes = []

    def route(self, pattern):
        def wrapper(handler):
            self.routes.append((pattern, handler))
            return handler
        return wrapper

    def recv(self, program, message, interface=None):

        def default_route(program, message=None, interface=None):
            # print('Unrecognized Message msg: {0}'.format(message))
            pass

        # run through route patterns looking for a match to handle the msg
        for pattern, handler in self.routes:
            # if pattern is a compiled regex, try matching it
            if hasattr(pattern, 'match') and pattern.match(message):
                break
            # if pattern is just a str, check for exact match
            if message == pattern:
                break
        else:
            # if no route matches, fall back to default handler
            handler = default_route

        handler(program, message, interface)
