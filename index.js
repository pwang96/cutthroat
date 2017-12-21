var ws;
var playerName;
var playerId;

$().ready(function () {
    $("#mainScreen").show()
    $("#playScreen").hide()
    $("#btnConnect").click(function () {
        playerName = $("#playerName").val()
        $("#status").text("connecting...");
        ws_url = "ws://" + location.host + "/connect"
        ws = new WebSocket(ws_url);
        ws.onopen = openHandler;
        ws.onmessage = messageHandler;
        ws.onerror = function (e) {
            $("#status").text(e.message);
        };
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
    });
    $("#btnDrawTile").click(function() {
        sendMessage(["draw_tile"]);
    })
});

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
        case("update"):
            var free_tiles = args[1];
            var players = args[2];
            $("#freeTiles").text("[" + free_tiles + "]");
            $("#table").empty();
            $.each(players, function(player_name,words){
                var entry = "<p>" + player_name + ": [" + words + "]</p>"
                $("#table").append(entry)
            });
            break
        case("p_joined"):
            var id = args[1];
            $("#status").text("joined the game");
            if(id == playerId)
                $("#btnJoin").css("visibility", "hidden");
            break
        case("p_gameover"):
            id = args[1];
            $("#player" + id).remove();
            if(id == playerId)
                $("#btnJoin").css("visibility", "visible");
            break
        case("p_score"):
            id = args[1];
            score = args[2];
            $("#player" + id + " .score").text(score);
            break
        case("top_scores"):
            $("#topScoresList").empty();
            players = args[1];
            for(var n = 0; n < players.length; n++) {
                name = players[n][0];
                score = players[n][1];
                color = players[n][2];
                addTopScore(color, name, score);
            }
    }
}
