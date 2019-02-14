var nats = require('nats').connect({'servers':['nats:iot-msg:4222']});
var express = require('express');
var http = require('http');
var redis = require('redis');

var app = express();
var client = redis.createClient('6379', 'rep-data');

nats.subscribe('trash-level', function(msg) {
    var rep = JSON.parse(msg);
    client.set(rep.can_id, rep.level);
    console.log('Saved report: ' + msg);
});

app.get('/reports/:can_id', function(req, res) {
    client.get(req.params.can_id, function(err, reply) {
        if (reply==null) {
            res.statusCode = 404;
            return res.send('Error: Trash Can not found\n');
        }
        console.log(reply);
        res.send('{"can_id":"' + req.params.can_id + '", "level":"'
        + reply + '"}');
    });
});

http.createServer(app).listen(9090, function() {
    console.log('Listening on port 9090');
});
