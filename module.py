from collections import OrderedDict
from dotenv import load_dotenv, dotenv_values
from flask import Flask
import hashlib
import pymysql.cursors


app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'


class funciones:
    def config():
        app.config['DEBUG'] = False
        app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
        app.run(debug=app.config['DEBUG'])
    def get_db_connection():
        load_dotenv()
        env_vars = dotenv_values()
        env = OrderedDict(env_vars)
        return pymysql.connect(
            host=env['HOST'],
            user=env['USERNAME'],
            password=env['PASSWORD'],
            database=env['DB'],
            cursorclass=pymysql.cursors.DictCursor,
            ssl_ca=env['SSL_CERT']
        )
    def encryptSHA256(code):
        string_bytes = code.encode('utf-8')
        sha256_hash = hashlib.sha256()
        sha256_hash.update(string_bytes)
        hash_encriptado = sha256_hash.hexdigest()
        return hash_encriptado