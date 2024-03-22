import os
from flask import Flask, flash, render_template, redirect, url_for, request, session
from flask_mysqldb import MySQL


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '-!Wsz169_128=@0'

# Configuración de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sitioweb'

# Inicialización de la extensión MySQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')


@app.route('/propiedades')
def propiedades():
    return render_template('propiedades.html')

def obtener_inmuebles_por_tipo(tipo):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM inmuebles WHERE tipo = %s", (tipo,))
    inmuebles = cur.fetchall()
    cur.close()
    return inmuebles

@app.route('/casas')
def casas():
    # Obtener inmuebles tipo "C" o "c" de la base de datos
    inmuebles_casas = obtener_inmuebles_por_tipo('C')
    # Renderizar la plantilla casas.html con los inmuebles obtenidos
    return render_template('casas.html', inmuebles=inmuebles_casas)

@app.route('/departamentos')
def departamentos():
    # Obtener inmuebles tipo "D" o "d" de la base de datos
    inmuebles_departamentos = obtener_inmuebles_por_tipo('D')
    # Renderizar la plantilla departamentos.html con los inmuebles obtenidos
    return render_template('departamentos.html', inmuebles=inmuebles_departamentos)

@app.route('/terrenos')
def terrenos():
    # Obtener inmuebles tipo "T" o "t" de la base de datos
    inmuebles_terrenos = obtener_inmuebles_por_tipo('T')
    # Renderizar la plantilla terrenos.html con los inmuebles obtenidos
    return render_template('terrenos.html', inmuebles=inmuebles_terrenos)


@app.route('/inmuebles')
def inmuebles():
    return render_template('inmuebles.html')

@app.route('/inmuebles/borrar', methods=['POST'])
def borrar_inmueble():
    if request.method == 'POST':
        # Obtener el ID del inmueble a borrar desde el formulario
        inmueble_id = request.form['txtID']

        # Ejecutar la consulta SQL para eliminar el inmueble
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM inmuebles WHERE id = %s", (inmueble_id,))
        mysql.connection.commit()
        cur.close()

        # Redireccionar a la página de administración de inmuebles
        return redirect(url_for('administradores'))

@app.route('/inmuebles/guardar', methods=['POST'])
def guardar_inmueble():
    if request.method == 'POST':
        try:
            _titulo = request.form['txtTitulo']
            _descripcion = request.form['txtDescripcion']
            _url = request.form['txtURL']
            _detalles = request.form['txtDetalles']
            _tipo = request.form['txtTipo']

            # Verificamos si se adjuntaron archivos
            archivos = request.files.getlist('txtImagen')

            # Guardamos los nombres de los archivos en una lista
            nombres_imagenes = []
            for i in range(1, 7):  # Iterar sobre los seis campos de imagen
                campo_imagen = f'txtImagen{i}'
                archivo = request.files[campo_imagen]
                if archivo.filename != '':  # Verificar si se adjuntó un archivo en el campo
                    # Guardamos el archivo en la carpeta de imágenes
                    archivo.save(os.path.join('static', 'img', archivo.filename))
                    nombres_imagenes.append(archivo.filename)
                else:
                    # Si no se adjuntó un archivo en el campo, añadimos None a la lista
                    nombres_imagenes.append(None)

            # Insertar en la base de datos
            with mysql.connection.cursor() as cursor:
                sql = "INSERT INTO `inmuebles` (`titulo`, `imagen1`, `imagen2`, `imagen3`, `imagen4`, `imagen5`, `imagen6`, `descripcion`, `url`, `detalles`, `tipo`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                datos = (_titulo, nombres_imagenes[0], nombres_imagenes[1], nombres_imagenes[2], nombres_imagenes[3], nombres_imagenes[4], nombres_imagenes[5], _descripcion, _url, _detalles, _tipo)
                cursor.execute(sql, datos)
                mysql.connection.commit()

            flash('Inmueble creado correctamente', 'success')

        except Exception as e:
            flash(f'Error al crear el inmueble: {str(e)}', 'error')

        return redirect('/propiedades')

    # Si la solicitud es GET, simplemente redirecciona a la página de administración
    return redirect('/administrador')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre_usuario = request.form['nuevo_usuario']
        contraseña = request.form['nueva_contraseña']

        # Verificar si el nombre de usuario ya está en uso
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (nombre_usuario,))
        usuario_existente = cur.fetchone()
        cur.close()

        if usuario_existente:
            flash('El nombre de usuario ya está en uso. Por favor, elige otro.', 'error')
            return redirect('/registro')
        else:
            # Insertar el nuevo usuario en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)", (nombre_usuario, contraseña))
            mysql.connection.commit()
            cur.close()
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect('/login')

    return render_template('registro.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['usuario']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, usuario, rol_id FROM usuarios WHERE usuario = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['loggedin'] = True
            session['username'] = user[1]  # Accede al nombre de usuario en la posición 1 de la tupla
            session['rol_id'] = user[2]  # Accede al ID del rol en la posición 2 de la tupla
            return redirect(url_for('administradores'))  # Redireccionar a la página principal después de iniciar sesión
        else:
            flash('Usuario o contraseña incorrectos. Inténtalo de nuevo.', 'error')

    # Si el usuario ya está logueado, redirigirlo directamente a la página de administradores
    if 'loggedin' in session:
        return redirect(url_for('administradores'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Eliminar todas las variables de sesión relacionadas con el inicio de sesión
    session.clear()
    # Redirigir al usuario a la página de inicio de sesión después de cerrar sesión
    return redirect(url_for('login'))

@app.route('/administradores', methods=['GET', 'POST'])
def administradores():
    if 'loggedin' in session and session['rol_id'] == 1:  # Verifica si el usuario está autenticado y es un administrador
        if request.method == 'POST':
            # Capturar los datos del formulario
            titulo = request.form['txtTitulo']
            descripcion = request.form['txtDescripcion']
            url = request.form['txtURL']
            detalles = request.form['txtDetalles']
            tipo = request.form['txtTipo']

            # Insertar los datos en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO inmuebles (titulo, descripcion, url, detalles, tipo) VALUES (%s, %s, %s, %s, %s)", (titulo, descripcion, url, detalles, tipo))
            mysql.connection.commit()
            cur.close()

            # Redirigir de vuelta a la página de administradores
            return redirect(url_for('administradores'))

        # Obtener los inmuebles de la base de datos
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM inmuebles")
        inmuebles = cur.fetchall()
        cur.close()

        # Si la solicitud es GET, simplemente renderiza la página de administradores con la lista de inmuebles
        return render_template('administradores.html', inmuebles=inmuebles)
    elif 'loggedin' in session:
        flash('No tienes permisos de administrador para acceder a esta página.', 'error')
        return redirect(url_for('index'))
    else:
        flash('Debes iniciar sesión como administrador para acceder a esta página.', 'error')
        return redirect(url_for('login'))





if __name__ == '__main__':
    app.run(debug=True)
