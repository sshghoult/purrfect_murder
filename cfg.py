import json


DATABASE = 'purrfect_murder'
# DB_HOST = '172.28.1.1'
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'AeDiwhvWj7_r'
DB_PORT = 3306
ACTIVE_CODES = set()


# CODES_GENERATOR = (reduce(lambda old, new: old + new, i) for i in itertools.cycle(itertools.product(string.ascii_uppercase, repeat=5)))
# CODES_GENERATOR = reduce(lambda old, new: old + new, random.choices(string.ascii_uppercase, k=5))


# TODO: will die after 5^33 lobbies running at the same time, cover it.


with open('source_tokens.json', 'r') as src:
    SOURCES = json.load(src)

# DB_ROOT_PASSWORD = 'PLACEHOLDER1'
