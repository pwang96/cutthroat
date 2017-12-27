import os
import asyncio
import json
from aiohttp import web
import aiohttp
import settings
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory
import re

from game import Game

async def handle(request):
    path = request.path
    file_path = 'index.html' if path == '/' else path[1:]
    pattern = re.compile('\.(\w*)$')
    non_html = re.findall(pattern, path)
    suffix = non_html[0] if non_html else 'html'
    try:
        with open(file_path, 'rb') as index:
            content_type = 'text/' + suffix
            return web.Response(body=index.read(), content_type=content_type)
    except FileNotFoundError:
        return web.Response(status=404)

async def wshandler(request):
    print("Connected")
    app = request.app
    game = app["game"]
    ws = web.WebSocketResponse()
    if ws.can_prepare(request).ok:
        print("web socket response can be prepared")
    else:
        print("there might be an issue with the web socket response")
    await ws.prepare(request)

    player = None
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            print("Got message: {}".format(data))

            if not player:
                if data[0] == "new_player":
                    player = game.new_player(data[1], ws)
            else:
                if player.active and data[0] == "play_word":
                    game.play_word(data[1].lower(), player)
                elif player.active and data[0] == "draw_tile":
                    game.draw_tile(player)
                elif player.active and data[0] == "add_bot":
                    if not game.bot:
                        game.create_bot()
                elif data[0] == "join":
                    if not game.running:
                        if not game.is_ready():
                            game.reset()

                        print("Starting game loop")
                        asyncio.ensure_future(game_loop(game))

                    game.join(player)

        elif msg.type == aiohttp.WSMsgType.CLOSE:
            print("Error: msg.type = CLOSE")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("Error: msg.type = ERROR")
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
app.router.add_route('GET', '/', handle)
app.router.add_route('GET', '/style.css', handle)
app.router.add_route('GET', '/index.js', handle)

# get port for heroku
port = int(os.environ.get('PORT', 5000))
web.run_app(app, port=port)