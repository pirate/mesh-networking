import socketio
import eventlet
from flask import Flask, render_template

sio = socketio.Server()
app = Flask(__name__)

@sio.on('chat message', namespace="/chat")
def test(sid, data):
    print('test', sid, data)
    sio.emit('chat message', data)

@app.route('/')
def index():
    """Serve the client-side application."""
    return open('static/index.html', 'r').read()

if __name__ == '__main__':
    # wrap Flask application with socketio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('', 80)), app)
