from collections import OrderedDict
from dotenv import load_dotenv, dotenv_values
from flask import Flask, render_template, request, redirect, session, jsonify
import hashlib
import pymysql.cursors
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'b1f21c5f7e90b9e6d3c3b12d916c6c82a8c0a72c97bdf8c918e3028b73cbb9a5'
CORS(app)

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
            host='dev-red-innova.mysql.database.azure.com',
            user='sofiadonoso',
            password='Sda.280899$',
            database='dev-regala-sonrisas',
            cursorclass=pymysql.cursors.DictCursor,
            ssl_ca='DigiCertGlobalRootCA.crt.pem'
        )

    def encryptSHA256(code):
        string_bytes = code.encode('utf-8')
        sha256_hash = hashlib.sha256()
        sha256_hash.update(string_bytes)
        hash_encriptado = sha256_hash.hexdigest()
        return hash_encriptado

####################################################################################################################
######################################################## OK
####################################################################################################################
@app.route('/')
def index():
    if 'email' in session:
        connection = funciones.get_db_connection()
        connection.begin()
        with connection.cursor() as cursor:
            userid=session.get('userid')
            print("userid: ", userid)
            cursor.execute(f"SELECT perfil, rut, CONCAT(nombres,' ', ap_pat, ' ', ap_mat) username, CASE perfil WHEN 1 THEN 'Beneficiario' WHEN 2 THEN 'Auspiciador' ELSE '' END  perfil_name FROM usuario WHERE id={userid}")
            query = cursor.fetchone()
            perfil=query['perfil']
            perfil_name=query['perfil_name']
            rut=query['rut']
            username=query['username']
            session['name']=username
            session['profile_id']=perfil
            session['profile']=perfil_name
        return render_template('index.html', userid=userid, perfil=perfil, perfil_name=perfil_name, rut=rut, username=username) 
    return render_template('login.html')
    
    
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    email = request.form['email']
    password = funciones.encryptSHA256(request.form['password'])
    try:
        connection = funciones.get_db_connection()
        connection.begin()
        with connection.cursor() as cursor:
            cursor.callproc('AUTH_MAIN_VALID', (email, password, 0, '', ''))
            cursor.execute("SELECT @_AUTH_MAIN_VALID_2 AS code, @_AUTH_MAIN_VALID_3 AS message, @_AUTH_MAIN_VALID_4 AS userid")
            result_main_valid = cursor.fetchone()
            code = result_main_valid['code']
            message = result_main_valid['message']
            userid=result_main_valid['userid']
            if code == 200:
                session['email'] = email
                session['userid'] = userid
                cursor.execute(f"SELECT perfil, rut, CONCAT(nombres,' ', ap_pat, ' ', ap_mat) username, CASE perfil WHEN 1 THEN 'Beneficiario' WHEN 2 THEN 'Auspiciador' ELSE '' END  perfil_name FROM usuario WHERE id={userid}")
                query = cursor.fetchone()
                perfil=query['perfil']
                perfil_name=query['perfil_name']
                rut=query['rut']
                username=query['username']
                return redirect('/')
            else:
                return render_template('login.html', alert_message=message)
    except Exception as e:
        if 'connection' in locals():
            connection.rollback()
        return render_template('login.html', alert_message=e)
    finally:
        if 'connection' in locals():
            connection.close()


@app.route('/projects', methods=['GET', 'POST'])
def projects():
    userid = session.get('userid')
    if not userid:
        print("Usuario no autentificado")
        return jsonify({"message": "Usuario no autenticado"}), 401  # Unauthorized
    try:
        connection = funciones.get_db_connection()
        with connection.cursor() as cursor:
            cursor.callproc('GET_PROYECTOS_BY_USERID', (userid,))
            data = cursor.fetchall()
            print("Python data: ", data)
            if not data:
                return jsonify({"message": "No hay proyectos disponibles"}), 404
            return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/register', methods=['GET', 'POST'])
def register(): 
    return render_template('register.html')


@app.route('/wishes', methods=['GET', 'POST'])
def wishes():
    idProject = request.args["idProject"]
    session['idProject']=idProject
    return render_template("wish.html", username=session.get('name'), profileName=session.get('profile'), profileID=session.get('profile_id'))


@app.route('/addProject', methods=['GET', 'POST'])
def addProject():
    userid = session.get('userid')
    name = request.form['name']
    descripcion = request.form['descripcion']
    print("Userid: ", userid)
    try:
        connection = funciones.get_db_connection()
        connection.begin()
        with connection.cursor() as cursor: 
            cursor.callproc('SET_PROYECTO', (userid, name, descripcion, 0, ''))
            cursor.execute("SELECT @_SET_PROYECTO_3 AS code, @_SET_PROYECTO_4 AS message")
            result = cursor.fetchone()
            code = result['code']
            message = result['message']
            print("Add project message: ", message)
            if code == 200:
                return redirect('/')
    except Exception as e:
        if 'connection' in locals():
            connection.rollback()
        return redirect('/')
    finally:
        if 'connection' in locals():
            connection.close()

####################################################################################################################
######################################################## NO OK
####################################################################################################################

@app.route('/validateWishes', methods=['GET', 'POST'])
def validateWishes():
    idProject = session.get('idProject')
    print("idProject Validate wishes: ", idProject)
    if not idProject:
        return redirect('/')
    try:
        connection = funciones.get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT A.id, CONCAT(B.nombres, " ", B.ap_pat, " ", B.ap_mat) usuario, A.nombre, A.detalle FROM deseo A LEFT JOIN usuario B ON A.id_usuario=B.id WHERE A.id_proyecto={idProject}')
            data = cursor.fetchall()
            print("Data wishes", data)
            if not data:
                return jsonify({"message": "No hay deseos disponibles"}), 400
            return jsonify(data), 200  # OK
    except Exception as e:
        print("Except validate wishes: ", e)
        if 'connection' in locals():
            connection.rollback()
        return jsonify({"error": str(e)}), 200
    finally:
        if 'connection' in locals():
            connection.close()



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
    email = request.form['email']
    psw = funciones.encryptSHA256(request.form['password'])
    if not email or not psw:
        return render_template('auth-gen.html', message="Faltan datos por completar")
    try:
        connection = funciones.get_db_connection()
        connection.begin()
        rut = session.get('dataUser', {}).get('rut')
        name = session.get('dataUser', {}).get('name')
        app1 = session.get('dataUser', {}).get('app1')
        app2 = session.get('dataUser', {}).get('app2')
        profile = session.get('dataUser', {}).get('profile')
        with connection.cursor() as cursor:
            cursor.callproc('CREATE_USER', (rut, email, psw, name, app1, app2, profile, 0, ''))
            cursor.execute("SELECT @_CREATE_USER_7 AS code, @_CREATE_USER_8 AS message")
            return render_template('login.html')
    except Exception as e:
            print("Error: ", e)
            if 'connection' in locals():
                connection.rollback()
            return render_template('auth-gen.html', alert_message='Ocurrio un error al autentificar al usuario. Intente mas tarde.')
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/deleteProject', methods=['GET', 'POST'])
def deleteProject():
    idProject = request.form['idProject']
    try:
        connection = funciones.get_db_connection()
        connection.begin()
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE proyecto SET estado='1' WHERE id={idProject}")
            connection.commit()
            return redirect('/')
    except Exception as e:
        if 'connection' in locals():
            connection.rollback()
        return redirect('/')
    finally:
        if 'connection' in locals():
            connection.close()






@app.route('/addWish', methods=['GET', 'POST'])
def addWish():
    idProject= session.get('idProject')
    userid = session.get('user_id')
    name= request.form['name']
    detail=request.form['detail']
    try:
        connection = funciones.get_db_connection()
        connection.begin()
        with connection.cursor() as cursor:
            cursor.callproc('SET_DESEO', (userid, idProject, name, detail, 0, ''))
            result = cursor.fetchone()
            code=result['_CODE']
            message=result['_MESS']
            return render_template('wish.html', username=session.get('name'), profileName=session['profile'], profileID=session['profile_id'], statuscode=code, statusmessage=message)
    except Exception as e:
        print(e)
        if 'connection' in locals():
            connection.rollback()
        return render_template('wish.html', username=session.get('name'), profileName=session['profile'], profileID=session['profile_id'])
    finally:
        if 'connection' in locals():
            connection.close()
            
if __name__ == '__main__':
    funciones.config()
