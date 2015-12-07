// (function() {  
  var socket = new WebSocket("ws://localhost:8080/websocket");

  var newnodeButton = $('button#newnode');
  var linkButton = $('button#link')
  var messageButton = $('button#message');

  var status = [0, 0, 0];

  var restoreState = function() {

    status = [0, 0, 0];
    linkButton.text("Link");
    messageButton.removeAttr("disabled");
  };

  var sendEvent = function() {

    if (status[0] == "link") {

      console.log(status);
      socket.send("addlink", JSON.stringify({source: status[1], target:status[2]}));
      status = ["link", status[2], 0];

    } else if (status[0] == "message") {
       socket.send("message", JSON.stringify({from:status[1], to:status[2]}));
       restoreState();
    } else {
      restoreState();
    }
  };
  newnodeButton.click(function (){
    addnode('abc');addnode('abcd');addnode('abcde');
  });

  linkButton.click(function (){
      
    if (status[0] == "link") restoreState();
    else {

      status[0] = "link";
      linkButton.text("Stop linking");
    }
  });

  messageButton.click(function (){

    restoreState();
    status[0] = "message";
    messageButton.attr("disabled", "disabled");
  });

  socket.onmessage = function(msg){
    var message = JSON.parse(msg.data);
    console.log('[WebSocket]: ' + message.message);
  };

  var width = 960,
      height = 500;

  var fill = d3.scale.category20();

  var force = d3.layout.force()
      .size([width, height])
      .nodes([]) // initialize with no nodes
      .linkDistance(30)
      .charge(-60)
      .on("tick", tick);

  var svg = d3.select("body").append("svg")
      .attr("viewBox", "0 0 " + width + " " + height)
      .attr("preserveAspectRatio", "xMidYMid meet")
      .on("mousemove", mousemove);

  svg.append("rect")
      .attr("width", width)
      .attr("height", height);

  var nodes = force.nodes(),
      links = force.links(),
      node = svg.selectAll(".node"),
      link = svg.selectAll(".link");

  var cursor = svg.append("circle")
      .attr("r", 30)
      .attr("transform", "translate(-100,-100)")
      .attr("class", "cursor");

  restart();

  function addnode(id, addr){
    for(var i=0; i<nodes.length; i++){
      if(nodes[i].id===id){
        console.log("node "+id+" already exists, not adding");
        return;
      }
    }

    console.log("adding node "+id);
    var randomX = Math.floor(Math.random()*$('svg').width());
    var randomY = Math.floor(Math.random()*$('svg').height());
    nodes.push({x: randomX, y: randomY, id: id, address: addr});
    restart();
    return node;
  }

  function findnode(id){
    return nodes.filter(function(node){
      return node.id===id;
    });
  }

  function findlink(source_id, target_id){
    return links.filter(function(link){
      return (link.source.id===source_id && link.target.id===target_id) ||
              (link.source.id===target_id && link.target.id===source_id);
    });
  }

  function addlink(source_id, target_id){
    // find or create nodes
    var source = findnode(source_id)[0] || addnode(source_id);
    var target = findnode(target_id)[0] || addnode(target_id);

    // find or create source and target node
    if(findlink(source_id,target_id).length){
      console.log("link "+source_id+" => "+target_id+" already exists, not adding");
      return;
    }
    console.log("adding link "+source_id+" => "+target_id);
    links.push({source: source, target: target});
    restart();
  }

  function mousemove() {
    cursor.attr("transform", "translate(" + d3.mouse(this) + ")");
  }

  function nodeClick(e) {

    if (status[0] !== 0) {

      if (status[1] === 0) {
          status[1] = e.id;

      } else if (status[2] === 0) {

          status[2] = e.id;
          sendEvent();
      }
    }

    console.log("Id: "+e.id+" Address: "+e.address);
  }

  function pulseNode(id, color) {
    var d3box = d3.select('[data-id="' + id + '"]');
    d3box.transition(500)
    .style('fill', color)
    .transition().duration(10000)
    .style('fill', '#eee');
  }

  function select(d) {
    if (d3SelectedElement) {
    d3SelectedElement.classed({'selected': false});
    }
    var d3box = d3.select('[data-id="' + d._id + '"]');
    d3box.classed({'selected': true});
    d3SelectedElement = d3box;
  }

  function tick() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  }

  function restart() {
    link = link.data(links);

    link.enter().insert("line", ".node")
        .attr("class", "link");

    node = node.data(nodes);

    node.enter().insert("circle", ".cursor")
        .attr("class", "node")
        .attr("r", 10)
        .attr("data-id", keyFn)
        .on("mousedown", nodeClick)
        .call(force.drag);

    force.start();
  }

  var keyFn = function(d){ return d.id; };
// })()
