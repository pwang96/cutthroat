var ws;
var playerName;
var playerId;

$().ready(function () {
    $("#mainScreen").show()
    $("#playScreen").hide()
    $("#btnConnect").click(function (){
        connect();
    });
    $("#btnDisconnect").click(function () {
        ws.close();
        $("#playScreen").hide();
        $("#mainScreen").show();
        $(document).unbind("keypress", keyHandler);
    });
    $("#btnJoin").click(function () {
        sendMessage(["join"]);
    });
    $("#btnPlayWord").click(function() {
        word = $("#word").val();
        sendMessage(["play_word", word]);
        $("#word").val('');
    });
    $("#btnDrawTile").click(function() {
        sendMessage(["draw_tile"]);
        $("#word").focus();
    });
    $("#btnAddBot").click(function() {
        sendMessage(["add_bot"]);
    });
    $("#playerName").keyup(function(event) {
        if (event.keyCode === 13) {
            $("#btnConnect").click();
        }
    });
    $("#word").keyup(function(event) {
        if (event.keyCode === 13) {
            $("#btnPlayWord").click();
        }
    });
    $(document).keyup(function(event) {
        if (event.keyCode === 9) {
            $("#btnDrawTile").click();
        }
    });
});

function connect() {
    playerName = $("#playerName").val()
    $("#status").text("connecting...");
    ws_url = "ws://" + location.host + "/connect"
    ws = new WebSocket(ws_url);
    ws.onopen = openHandler;
    ws.onmessage = messageHandler;
    ws.onerror = function (e) {
        $("#status").text(e.message);
    };
}

function sendMessage(msgArray) {
    var msg = JSON.stringify(msgArray);
    ws.send(msg);
}

function openHandler(e){
    $("#status").text("connected to server");
    playerName = $('#playerName').val();
    sendMessage(["new_player", playerName]);
    $("#mainScreen").hide();
    $("#playScreen").show();
}

function messageHandler(e){
    //$("#status").text(e.data);
    args = JSON.parse(e.data);
    var cmd = args[0];

    switch(cmd){
        case("handshake"):
            $("#username").text(args[1]);
            playerId = args[2];
            break

        case("game_full"):
            $("#notification").text("Sorry! The game is full.")
            break

        case("update_names"):
            var names = args[1];
            $("#currentPlayers").empty();
            $.each(names, function(index, val) {
                $("#currentPlayers").append("<p>" + val + "</p>");
            });
            break

        case("update"):
            var free_tiles = args[1];
            var players = args[2];
            $("#freeTiles").text("Free tiles: [" + free_tiles + "]");
            $("#table").empty();
            $("#currentPlayers").empty();
            $("#currentPlayers").append("<h5>Current Players</h5>");
            $.each(players, function(player_name, words){
                var entry = "<p>" + player_name + ": [" + words + "]</p>";
                $("#table").append(entry);
                $("#currentPlayers").append("<p>" + player_name + "</p>");
            });
            break

        case("p_joined"):
            var id = args[1];
            var name = args[2];
            if(id == playerId) {
                $("#btnJoin").css("visibility", "hidden");
                $("#status").css("visibility", "hidden");
            }
            $("#notification").text(name + " has joined!");
            break

        case("valid_word"):
            var word = args[1];
            var name = args[2];
            $("#notification").text(name + " played " + word);
            break

        case("invalid_word"):
            var word = args[1];
            $("#notification").text(word + " is not valid!");
            break

        case("scores"):
            var scores = args[1];
            $("#scoresList").empty();
            for (var i = 0; i < scores.length; i++) {
                var name = scores[i][0];
                var score = scores[i][1];
                $("#scoresList").append("<p>" + name + ": " + score + "</p>");
            }
            break

        case("dc"):
            var name = args[1];
            $("#notification").text(name + " has disconnected");
            break

        case("p_gameover"):
            id = args[1];
            $("#player" + id).remove();
            if(id == playerId)
                $("#btnJoin").css("visibility", "visible");
            break
    }
}
