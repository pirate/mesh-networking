# server
restify = require 'restify'
server = restify.createServer()

# for random ids
crypto = require 'crypto'

# socket.io
socketio = require 'socket.io'
io = socketio.listen server

printData = (data) ->
  console.log "socket message: "
  console.dir data

# handle messages from cliens
io.sockets.on 'connection', (socket) ->
  socket.on 'addnode', printData
  socket.on 'addlink', printData

setInterval addRandomNode, 5000
addRandomNode = ->
  randomId = crypto.randomBytes(Math.ceil(16/2)).toString('hex').slice(0,16)
  io.emit 'addnode', JSON.stringify({id: randomId})

# cors proxy and body parser
server.use restify.bodyParser()
server.use restify.fullResponse() # set CORS, eTag, other common headers

server.get /\/*$/, restify.serveStatic directory: './public', default: 'index.html'

server.listen (process.env.PORT or 8080), ->
  console.info "[%s] #{server.name} listening at #{server.url}", process.pid
