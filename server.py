import os
import asyncio
import json
from aiohttp import web
import settings
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory

from game import Game

async def handle(request):
    ALLOWED_FILES = ["index.html", "style.css"]
    name = request.match_info.get('name', 'index.html')
    if name in ALLOWED_FILES:
        try:
            with open(name, 'rb') as index:
                return web.Response(body=index.read(), content_type='text/html')
        except FileNotFoundError:
            pass
    return web.Response(status=404)


async def wshandler(request):
    print("Connected")
    app = request.app
    game = app["game"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player = None
    while True:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            print("Got message %s" % msg.data)

            data = json.loads(msg.data)
            print("message data: {}".format(data))
            if not player:
                if data[0] == "new_player":
                    player = game.new_player(data[1], ws)
            else:
                if player.active and data[0] == "play_word":
                    game.play_word(data[1].lower(), player)
                elif player.active and data[0] == "draw_tile":
                    game.draw_tile()
                elif player.active and data[0] == "add_bot":
                    if not game.bot:
                        game.create_bot()
                elif data[0] == "join":
                    if not game.running:
                        game.reset()

                        print("Starting game loop")
                        asyncio.ensure_future(game_loop(game))

                    game.join(player)

        elif msg.tp == web.MsgType.close:
            break

    if player:
        game.player_disconnected(player)

    print("Closed connection")
    return ws

async def game_loop(game):
    game.running = True
    while True:
        if game.finished:
            print("Stopping game loop")
            break
        await asyncio.sleep(1./settings.GAME_SPEED)
    game.running = False


event_loop = asyncio.get_event_loop()
event_loop.set_debug(True)

# app = web.Application()
app = web.Application(middlewares=[toolbar_middleware_factory])
aiohttp_debugtoolbar.setup(app)

app["game"] = Game()

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/{name}', handle)
app.router.add_route('GET', '/', handle)

# get port for heroku
port = int(os.environ.get('PORT', 5000))
web.run_app(app, port=port)