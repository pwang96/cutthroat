var ws;
var playerName;
var playerId;

$().ready(function () {
    // only show the main screen on arrival
    $("#mainScreen").show();
    $("#waitingScreen").hide();
    $("#playScreen").hide();

    // initialize button handlers
    initializeButtons();
});

function connect() {
    playerName = $("#playerName").val()
    // $("#status").text("connecting...");
    ws_url = "ws://" + location.host + "/connect";
    console.log(location.host);
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
    //$("#status").text("connected to server");
    playerName = $('#playerName').val();
    sendMessage(["new_player", playerName]);
    $("#mainScreen").hide();
    $("#waitingScreen").show();
}

function initializeButtons() {
    $("#btnConnect").click(function (){
        connect();
    });

    $("#btnCreateGame").click(function () {
        sendMessage(["create_game"]);
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

    $("#btnReturnToWaitingRoom").click(function() {
        sendMessage(["return_to_waiting_room"]);
        $("#playScreen").hide();
        $("#waitingScreen").show();
        $("#freeTiles").empty();
        $("#freeTiles").text("Free tiles:");
    });

    $("#btnAddBot").click(function() {
        sendMessage(["add_bot"]);
    });

    $("#btnRemoveBot").click(function() {
        sendMessage(["remove_bot"]);
    })

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
            var disabled = $("#btnDrawTile").attr('disabled');
            if (typeof disabled === typeof undefined || disabled === false) {
                $("#btnDrawTile").click();
            }
        }
    });
}

function messageHandler(e){
    //$("#status").text(e.data);
    args = JSON.parse(e.data);
    var cmd = args[0];
    console.log(args)

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

        case("render_active_games"):
            var games = args[1];
            let n = 1;
            $("#activeGames").empty();

            $.each(games, function(game_id, players) {
                jQuery('<div/>', {
                    id: game_id,
                    text: 'Game ' + n
                }).appendTo('#activeGames');
                n++;

                jQuery('<button/>', {
                    id: game_id,
                    class: 'btnJoin',
                    text: 'Join!',
                    click: function () {sendMessage(["join", $(this).attr('id')]);}
                }).appendTo('#' + game_id);

                jQuery('<div/>', {
                    id: 'currentPlayers' + game_id,
                    text: 'Players in this game: ' + players
                }).appendTo('#' + game_id);
            });
            break

        case("joined_game"):
            $("#waitingScreen").hide();
            $("#playScreen").show();
            break

        case("update"):
            var free_tiles = args[1];
            var num_tiles_left = args[2];
            var players = args[3];
            var drawer = args[4];
            $("#freeTiles").text("Free tiles:");
            free_tiles.forEach(function(tile) {
                console.log(tile);
                $("#freeTiles").append("<img src='/static/letter-" + tile + ".svg' height='35px' width='35px' />")
            });
            $("#numTilesLeft").text(num_tiles_left + " tiles left.");
            $("#table").empty();
            $.each(players, function(player_name, words){
                if (player_name == playerName) {
                    var entry = "<strong><p>" + player_name + ": [" + words + "]</p></strong>";
                    $("#table").append(entry);
                    return false;
                }
            });
            $.each(players, function(player_name, words){
                if (player_name != playerName) {
                    var entry = "<p>" + player_name + ": [" + words + "]</p>";
                    $("#table").append(entry);
                }
            });

            if (drawer != playerName) {
                $('#btnDrawTile').attr('disabled', true);
            } else {
                $('#btnDrawTile').removeAttr('disabled');
            }
            break

        case("p_joined"):
            var id = args[1];
            var name = args[2];
            if(id == playerId) {
                $("#btnJoin").css("visibility", "hidden");
                $("#status").css("visibility", "hidden");
            }
            $.bootstrapGrowl(name + " has joined!",{
                type: 'info',
                delay: 1000,
            });
            break

        case("valid_word"):
            var word = args[1];
            var name = args[2];
            $.bootstrapGrowl(name + " played " + word,{
                type: 'info',
                delay: 1000,
            });
            break

        case("invalid_word"):
            var word = args[1];
            $.bootstrapGrowl(word + " is not valid!",{
                type: 'info',
                delay: 1000,
            });
            break

        case("scores"):
            var scores = args[1];
            $("#scoresList").empty();
            for (var i = 0; i < scores.length; i++) {
                var name = scores[i][0];
                var score = scores[i][1];
                if (name == playerName) {
                    $("#scoresList").append("<strong><p>" + name + ": " + score + "</p></strong>");
                    break;
                }
            }
            for (var j = 0; j < scores.length; j++) {
                var name = scores[j][0];
                var score = scores[j][1];
                if (name != playerName) {
                    $("#scoresList").append("<p>" + name + ": " + score + "</p>");
                }
            }
            break

        case("dc"):
            var name = args[1];
            $.bootstrapGrowl(name + " has disconnected!",{
                type: 'info',
                delay: 1000,
            });
            break

        case("p_gameover"):
            id = args[1];
            $("#player" + id).remove();
            if(id == playerId)
                $("#btnJoin").css("visibility", "visible");
            break
    }
}
