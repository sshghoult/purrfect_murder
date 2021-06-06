import json
import cfg
import logging
from functools import reduce
import itertools
import string
import random


class NoneDict(dict):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError or ValueError:
            return None


async def check_source(data: dict):
    logging.debug(msg=f'check_source: data={data}')
    if data['data_source_token'] in cfg.SOURCES:
        if 'source_validity_proof_token' in data:
            if cfg.SOURCES[data['data_source_token']] == data['source_validity_proof_token']:
                pass
            else:
                raise ValueError('Invalid source_validity_proof_token')
        else:
            raise ValueError('source_validity_proof_token not found')
    else:
        raise ValueError('Invalid data_source_token')


async def check_id_user_reg(data: dict):
    try:
        if data['data_source_token'] == 'plain':
            return dict(plain_id=data['plain_id'], vk_id=None, telegram_id=None)
        elif data['data_source_token'] == 'vk':
            return dict(vk_id=data['vk_id'], plain=None, telegram_id=None)
        elif data['data_source_token'] == 'telegram':
            return dict(telegram_id=data['telegram_id'], vk_id=None, plain=None)
    except KeyError:
        raise ValueError('Invalid id type')



def gen_code():
    while True:
        code = reduce(lambda old, new: old + new, random.choices(string.ascii_uppercase, k=5))
        while code in cfg.ACTIVE_CODES:
            code = reduce(lambda old, new: old + new, random.choices(string.ascii_uppercase, k=5))
        cfg.ACTIVE_CODES.add(code)
        yield code


CODES_GENERATOR = gen_code()