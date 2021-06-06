from aiohttp import web
import logging
import handlers


def run_main():
    app = web.Application()
    logging.basicConfig(level=logging.DEBUG)

    app.add_routes([web.post('/user', handlers.post_user), web.post('/lobby', handlers.post_lobby),
                    web.post('/lobby/user', handlers.post_lobby_user), web.post('/lobby/start', handlers.post_lobby_start),
                    web.post('/lobby/accept_kill', handlers.post_lobby_accept_kill), web.get('/lobby', handlers.get_lobby)])

    web.run_app(app, port=8080, access_log=logging.getLogger('aiohttp.server'))


run_main()
