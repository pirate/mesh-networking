from flask import Flask
from flask_sockets import Sockets


app = Flask(__name__)
sockets = Sockets(app)

@sockets.route('/echo')
def echo_socket(ws):
    while True:
        message = ws.receive()
        ws.send(message)

@app.route('/')
def index():
    """Serve the client-side application."""
    return open('static/index.html', 'r').read()

if __name__ == '__main__':
    # wrap Flask application with socketio's middleware
    app.start()
