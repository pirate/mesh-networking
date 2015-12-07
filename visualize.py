from bottle import request, run, route, template, Bottle, abort, static_file
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler

app = Bottle()

host, port = ("0.0.0.0", 8080)

@app.route('/')
def index():
    return template('static/index.html', host=host, port=port)

@app.get('/static/<path:path>')
def static_files(path):
    return static_file(path, root='static/')



@app.route('/websocket_test')
def index():
    return template('static/websocket_test.html', host=host, port=port)

@app.route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    while True:
        try:
            message = wsock.receive()
            wsock.send("Your message was: %r" % message)
        except WebSocketError:
            break


server = WSGIServer((host, port), app, handler_class=WebSocketHandler)
print "Starting bottle WSGI + Websocket server %s:%s..." % (host, port)
server.serve_forever()
