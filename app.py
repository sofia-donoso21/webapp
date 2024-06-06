from flask import Flask, render_template, request, redirect, session, jsonify
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv, dotenv_values
import pymysql.cursors
from collections import OrderedDict
import string
import random
import smtplib


app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'


# CONFIG, para la configuracion de la aplicacion
def config():
    app.config['DEBUG'] = False
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
    app.run(debug=app.config['DEBUG'])

# GET_DB_CONNECTION, para la establecer la conexion de bbdd
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

# ENCRYPTSHA256, para encriptar formato SHA256 la password
def encryptSHA256(code):
    string_bytes = code.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(string_bytes)
    hash_encriptado = sha256_hash.hexdigest()
    return hash_encriptado




@app.route('/')
def index():
    profile = session.get('dataUser', {}).get('profile')
    profileName=''
    if (profile == 1):
        profileName='Beneficiario' 
    profileName='Auspiciador' 
    if 'email' in session:
        return render_template('index.html', username=session.get('dataUser', {}).get('username'), profile=profileName)
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = encryptSHA256(request.form['password'])
        if not email or not password:
            alert_message = "Usuario y contraseña son obligatorios."
            return render_template('login.html', alert_message=alert_message)
        try:
            connection = get_db_connection()
            connection.begin()
            with connection.cursor() as cursor:
                cursor.callproc('AUTH_MAIN_VALID', (email, password, 0, '', ''))
                cursor.execute("SELECT @_AUTH_MAIN_VALID_2 AS code, @_AUTH_MAIN_VALID_3 AS message, @_AUTH_MAIN_VALID_4 AS userid")
                result_main_valid = cursor.fetchone()
                code = result_main_valid['code']
                print("sttaus code:", code)
                message = result_main_valid['message']
                if code == 200:
                    session['email'] = email
                    session['user_id'] = result_main_valid['userid']
                    return redirect('/')
                return render_template('login.html', alert_message=message)
        except Exception as e:
            if 'connection' in locals():
                connection.rollback()
            return render_template('login.html', alert_message='Ocurrio un error al autentificar al usuario. Intente mas tarde.')
        finally:
            if 'connection' in locals():
                connection.close()
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('email', None)
    session.pop('dataUser', None)
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register(): 
    return render_template('register.html')


@app.route('/validate', methods=['GET', 'POST'])
def registerPage(): 
    rut = request.form['rut']
    name = request.form['name']
    app1 = request.form['app1']
    app2 = request.form['app2']
    profile = request.form['profile']
    profile_id = int(profile)
    if not rut or not name or not app1 or not app2 or profile_id == 0:
        return render_template('register.html', message="Faltan datos por completar")
    datos_usuario = {
    'rut': rut,
    'name': name,
    'app1': app1,
    'app2': app2,
    'profile': profile,
    'username': str(f"{name} {app1} {app2}") 
    }
    session['dataUser'] = datos_usuario
    return render_template('auth-gen.html', data=datos_usuario)


@app.route('/user', methods=['GET', 'POST'])
def user(): 
    print("data user: ", session.get('dataUser'))
    email = request.form['email']
    psw = encryptSHA256(request.form['password'])
    if not email or not psw:
        return render_template('auth-gen.html', message="Faltan datos por completar")
    try:
        connection = get_db_connection()
        connection.begin()
        rut = session.get('dataUser', {}).get('rut')
        name = session.get('dataUser', {}).get('name')
        app1 = session.get('dataUser', {}).get('app1')
        app2 = session.get('dataUser', {}).get('app2')
        profile = session.get('dataUser', {}).get('profile')
        with connection.cursor() as cursor:
            cursor.callproc('CREATE_USER', (rut, email, psw, name, app1, app2, profile, 0, ''))
            cursor.execute("SELECT @_CREATE_USER_7 AS code, @_CREATE_USER_8 AS message")
            result_main_valid = cursor.fetchone()
            return render_template('login.html')
    except Exception as e:
            print("Error: ", e)
            if 'connection' in locals():
                connection.rollback()
            return render_template('auth-gen.html', alert_message='Ocurrio un error al autentificar al usuario. Intente mas tarde.')
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/projects', methods=['GET', 'POST'])
def projects():
    userid =  session.get('user_id')
    print("Userid: ", userid)
    if not userid:
        return render_template('login.html')
    
    try:
        connection = get_db_connection()
        connection.begin()
        with connection.cursor() as cursor:
            cursor.callproc('GET_PROYECTOS_BY_USERID', (userid,))
            data = cursor.fetchall()
            print(data[0])
            return data
    except Exception as e:
        print("Error: ", e)
        if 'connection' in locals():
            connection.rollback()
        return render_template('login.html')

    finally:
        if 'connection' in locals():
            connection.close()

    # projectsJSON = [{
    #     'id': 1,
    #     'username': 'Sofia',
    #     'name': 'test',
    #     'detail' : 'test',
    #     'date': '2024-04-29 17:37:25',
    #     'percent': '50%'
    # }]
    # return jsonify(projectsJSON)



if __name__ == '__main__':
    config()
