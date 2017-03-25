from bottle import request, run, route, template, Bottle, abort, static_file
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
import simplejson as json

app = Bottle()

host, port = ("0.0.0.0", 8080)

@app.route('/')
def index():
    html = 'static/index.html'
    print "[HTTP]: %s" % html
    return template(html, host=host, port=port)

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
            print "[WebSocket]: %s" % message
            wsock.send(json.dumps({'message': message}))
        except WebSocketError:
            break


server = WSGIServer((host, port), app, handler_class=WebSocketHandler)
print "Starting bottle WSGI + Websocket server %s:%s..." % (host, port)
server.serve_forever()
