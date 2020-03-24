import os, asyncio, json, aiohttp, re, sys, argparse
from aiohttp import web
import settings
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory
from game_controller import GameController

async def handle(request):
    path = request.path
    # print(path)
    file_path = 'index.html' if path == '/' else path[1:]
    pattern = re.compile('\.(\w*)$')
    non_html = re.findall(pattern, path)
    suffix = non_html[0] if non_html else 'html'
    # print(file_path)
    try:
        with open('Web/' + file_path, 'rb') as index:
            content_type = 'text/' + suffix
            return web.Response(body=index.read(), content_type=content_type)
    except FileNotFoundError:
        return web.Response(status=404)

async def wshandler(request):
    print("Connected")
    app = request.app
    controller = app["controller"]
    ws = web.WebSocketResponse(autoping=True, heartbeat=5)
    await ws.prepare(request)

    player = None
    game = None
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            # print("Got message: {}".format(data))

            if not player:
                if data[0] == "new_player":
                    player = controller.new_player(data[1], ws)
            else:
                if data[0] == "create_game":
                    game = controller.create_new_game()
                    print('create_game clicked: new game has id {}'.format(game.game_id))
                    if not game.running:
                        print('starting game loop for game_id {}'.format(game.game_id))
                        asyncio.ensure_future(game_loop(game))
                    controller.add_to_existing_game(game.game_id, player)
                elif data[0] == "join":
                    game_id = data[1]
                    game = controller.add_to_existing_game(game_id, player)

                elif player.active and data[0] == "play_word":
                    game.play_word(data[1].lower(), player)
                elif player.active and data[0] == "draw_tile":
                    game.draw_tile(player)
                elif player.active and data[0] == "add_bot":
                    if not game.bot:
                        game.create_bot()
                elif player.active and data[0] == "remove_bot":
                    game.remove_bot()

                elif data[0] == "return_to_waiting_room":
                    print('clicked return_to_waitin_room')
                    game = None
                    controller.player_disconnected(player)
                    controller.add_to_waiting_area(player)
                    controller.render_active_games()
        elif msg.type == aiohttp.WSMsgType.CLOSE:
            print("Error: msg.type = CLOSE")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("Error: msg.type = ERROR")
            break

    if player and game:
        controller.player_disconnected(player)

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

async def simple(request):
    return web.Response(text="Simple answer")


def init(debug):
    app = web.Application()
    app['controller'] = GameController(debug=debug)
    app.router.add_get('/', handle)
    app.router.add_get('/style.css', handle)
    app.router.add_get('/index.js', handle)
    app.router.add_get('/connect', wshandler)
    app.router.add_static('/static/', 'static/')

    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', const=1, type=int, default=5000)
    parser.add_argument("--debug", help="show debug messages", action="store_true")
    args = parser.parse_args()
    if args.port:
        port = args.port

    event_loop = asyncio.get_event_loop()
    event_loop.set_debug(True)

    # get port for heroku
    port = int(os.environ.get('PORT', args.port))
    web.run_app(init(True), port=port)
