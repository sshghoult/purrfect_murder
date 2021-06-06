from aiohttp import web
import db_functions
import logic_functions
import json
import logging
import cfg


async def post_user(request: web.Request):
    """
    coroutine-handler for the POST /user request;
    required json format:
    {
    "data_source_token": <>,
    "source_validity_proof_token": <>,
    "id": <> (source-depended id of the user)
    }
    :param request: web.Request object obtained from the aiohttp request resolver
    :return: web.json_response with result and commentary on it
    """
    # TODO: add format of returned json here later

    data = await request.json()
    # check_data_source and its validity and if passed id source cooperates with them
    try:
        await logic_functions.check_source(data)
        reg_data = await logic_functions.check_id_user_reg(data)
        logging.debug(msg=f'post_user: reg_data={reg_data}')
        await db_functions.add_user(reg_data)
    except ValueError as e:
        logging.debug(msg=f'post_user: {e.__class__, e}')
        return web.json_response(json.dumps(f"""{{"result_reason": "{str(e)}"}}"""), status=400, reason='Bad Request')
    else:
        return web.json_response(json.dumps(f"""{{"result_reason": "OK"}}"""), status=200, reason='OK')


async def post_lobby(request: web.Request):
    """
    coroutine-handler for the POST /lobby request;
    required json format:
    {
    "data_source_token": <>,
    "source_validity_proof_token": <>,
    }
    :param request: web.Request object obtained from the aiohttp request resolver
    :return: web.json_response with result and commentary on it
    """
    data = await request.json()

    try:
        await logic_functions.check_source(data)
        code = next(logic_functions.CODES_GENERATOR)
        await db_functions.add_lobby(code)
    except ValueError as e:
        return web.json_response(json.dumps(f"""{{"result_reason": "{str(e)}"}}"""), status=400, reason='Bad Request')
    else:
        return web.json_response(json.dumps(f"""{{"result_reason": "OK", "lobby_code": {code}}}"""), status=200, reason='OK')


async def post_lobby_user(request: web.Request):
    data = await request.json()
    """
    coroutine-handler for the POST /lobby/user request;
    required json format:
    {
    "data_source_token": <>,
    "source_validity_proof_token": <>,
    "lobby_code": <>
    "id": <> 
    }
    :param request: web.Request object obtained from the aiohttp request resolver
    :return: web.json_response with result and commentary on it
    """
    try:
        await logic_functions.check_source(data)
        await db_functions.user_joined_lobby(data['lobby_code'], data['id'])
    except ValueError as e:
        return web.json_response(json.dumps(f"""{{"result_reason": "{str(e)}"}}"""), status=400, reason='Bad Request')
    else:
        return web.json_response(json.dumps(f"""{{"result_reason": "OK"}}"""), status=200, reason='OK')


async def post_lobby_start(request: web.Request):
    data = await request.json()
    """
    coroutine-handler for the POST /lobby/start request;
    required json format:
    {
    "data_source_token": <>,
    "source_validity_proof_token": <>,
    "lobby_code": <>
    }
    :param request: web.Request object obtained from the aiohttp request resolver
    :return: web.json_response with result and commentary on it
    """
    try:
        await logic_functions.check_source(data)
        await db_functions.lobby_started(data['lobby_code'])
    except ValueError as e:
        return web.json_response(json.dumps(f"""{{"result_reason": "{str(e)}"}}"""), status=400, reason='Bad Request')
    else:
        return web.json_response(json.dumps(f"""{{"result_reason": "OK"}}"""), status=200, reason='OK')


async def post_lobby_kill(request: web.Request):
    pass


async def post_lobby_accept_kill(request: web.Request):
    data = await request.json()
    """
    coroutine-handler for the POST /lobby/accept_kill request;
    required json format:
    {
    "data_source_token": <>,
    "source_validity_proof_token": <>,
    "id": <> (source-depended id of the victim)
    }
    :param request: web.Request object obtained from the aiohttp request resolver
    :return: web.json_response with result and commentary on it
    """
    try:
        await logic_functions.check_source(data)
        await db_functions.accept_kill(data["id"])
    except ValueError as e:
        return web.json_response(json.dumps(f"""{{"result_reason": "{str(e)}"}}"""), status=400, reason='Bad Request')
    else:
        return web.json_response(json.dumps(f"""{{"result_reason": "OK"}}"""), status=200, reason='OK')
    # TODO: delete code from the cfg set when lobby is killed


async def get_lobby(request: web.Request):
    data = await request.json()
    """
    coroutine-handler for the GET /lobby request;
    required json format:
    {
    "data_source_token": <>,
    "source_validity_proof_token": <>,
    "lobby_code": <>
    }
    :param request: web.Request object obtained from the aiohttp request resolver
    :return: web.json_response with result and commentary on it
    """
    try:
        await logic_functions.check_source(data)
        result = await db_functions.get_lobby_info(data["lobby_code"])
    except ValueError as e:
        return web.json_response(json.dumps(f"""{{"result_reason": "{str(e)}"}}"""), status=400, reason='Bad Request')
    else:
        return web.json_response(json.dumps(result), status=200, reason='OK')
