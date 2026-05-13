from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
# herramientas de seguridad
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuración de la Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tienda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
# Clave secreta obligatoria para mantener las sesiones de los usuarios seguras
# app.config['SECRET_KEY'] = 'mi_clave_secreta_super_segura'
import secrets
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Si alguien sin permiso intenta entrar, lo manda aquí
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# BD

# Tabla 1: Usuarios
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # Nueva columna para roles: 'admin' o 'cliente'
    rol = db.Column(db.String(20), default='cliente')

# Tabla 2: Prendas
class Prenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    talla = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=1)
    imagen = db.Column(db.String(255), nullable=False)

# Crear tablas al iniciar
with app.app_context():
    # # db.create_all()


    # Lógica para manejar cambios en el modelo y evitar errores de base de datos desactualizada
    try:
        db.create_all()
        # Intentamos buscar el admin para verificar que la columna 'rol' exista
        admin_existente = Usuario.query.filter_by(rol='admin').first()
    except Exception:
        # Si falla (ej. falta la columna 'rol'), limpiamos y recreamos la base de datos
        db.drop_all()
        db.create_all()
        admin_existente = None

    # Agregamos un usuario administrador por defecto si no existe ninguno en la BD.
    # if not Usuario.query.filter_by(rol='admin').first():
    if not admin_existente:
        # Credenciales iniciales: correo 'admin@tienda.com' y contraseña 'admin123'
        password_admin = generate_password_hash('admin123')
        usuario_admin = Usuario(
            # nombre='Administrador Central',
            nombre='Administrador',
            correo='admin@tienda.com',
            password=password_admin,
            rol='admin'
        )
        db.session.add(usuario_admin)
        db.session.commit()

    # Agregamos productos de prueba (dummies) si la tabla está vacía
    if Prenda.query.count() == 0:
        p1 = Prenda(nombre='Camiseta Básica', descripcion='Camiseta de algodón esencial', talla='M', color='Negro', precio=15.99, stock=50, imagen='default.png')
        p2 = Prenda(nombre='Pantalón Vaquero', descripcion='Jeans resistentes de corte recto', talla='30', color='Azul', precio=39.95, stock=30, imagen='default.png')
        p3 = Prenda(nombre='Sudadera Hoodie', descripcion='Gris jaspeado con capucha', talla='L', color='Gris', precio=25.50, stock=20, imagen='default.png')
        db.session.add_all([p1, p2, p3])
        db.session.commit()


# Catálogo, Búsqueda
@app.route('/')
def index():
    palabra_busqueda = request.args.get('buscar')

    if palabra_busqueda:
        # Filtramos las prendas que contengan la palabra buscada
        prendas_guardadas = Prenda.query.filter(Prenda.nombre.contains(palabra_busqueda)).all()
        prendas_destacadas = []
    else:
        # Catálogo normal y las 3 últimas como destacadas
        prendas_guardadas = Prenda.query.all()
        prendas_destacadas = Prenda.query.order_by(Prenda.id.desc()).limit(3).all()

    return render_template('index.html',
                           prendas=prendas_guardadas,
                           destacadas=prendas_destacadas,
                           busqueda=palabra_busqueda)


# ruta login

@app.route('/inventario')
@login_required
def inventario():
    # Verificamos si el usuario es administrador
    if current_user.rol != 'admin':
        flash('No tienes permisos para acceder al inventario.')
        return redirect(url_for('index'))
    prendas_guardadas = Prenda.query.all()
    return render_template('inventario.html', prendas=prendas_guardadas)

@app.route('/agregar', methods=['GET', 'POST'])
@login_required
def agregar_prenda():
    # Verificamos si el usuario es administrador
    if current_user.rol != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        file = request.files['imagen']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = 'default.png'

        nueva_prenda = Prenda(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            talla=request.form['talla'],
            color=request.form['color'],
            precio=float(request.form['precio']),
            stock=int(request.form['stock']),
            imagen=filename
        )
        db.session.add(nueva_prenda)
        db.session.commit()
        return redirect(url_for('inventario'))

    return render_template('agregar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_prenda(id):
    # Verificamos si el usuario es administrador
    if current_user.rol != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    prenda_a_editar = Prenda.query.get_or_404(id)

    if request.method == 'POST':
        prenda_a_editar.nombre = request.form['nombre']
        prenda_a_editar.descripcion = request.form['descripcion']
        prenda_a_editar.talla = request.form['talla']
        prenda_a_editar.color = request.form['color']
        prenda_a_editar.precio = float(request.form['precio'])
        prenda_a_editar.stock = int(request.form['stock'])

        file = request.files['imagen']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            prenda_a_editar.imagen = filename

        db.session.commit()
        return redirect(url_for('inventario'))

    return render_template('editar.html', prenda=prenda_a_editar)

@app.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_prenda(id):
    # Verificamos si el usuario es administrador
    if current_user.rol != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('index'))

    prenda_a_eliminar = Prenda.query.get_or_404(id)
    db.session.delete(prenda_a_eliminar)
    db.session.commit()
    return redirect(url_for('inventario'))


@app.route('/prenda/<int:id>')
def detalle_prenda(id):
    prenda_seleccionada = Prenda.query.get_or_404(id)
    return render_template('detalle.html', prenda=prenda_seleccionada)


# registro

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']

        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('Ese correo ya está registrado. Intenta iniciar sesión.')
            return redirect(url_for('registro'))

        # password_encriptada = generate_password_hash(password, method='pbkdf2:sha256')
        # Usamos el método por defecto para mayor compatibilidad
        password_encriptada = generate_password_hash(password)

        # nuevo_usuario = Usuario(nombre=nombre, correo=correo, password=password_encriptada)
        # El primer usuario registrado será admin automáticamente para facilitar pruebas
        # rol_asignado = 'admin' if Usuario.query.count() == 0 else 'cliente'
        
        # Al tener ya un admin creado por defecto en el arranque, todos los nuevos registros serán clientes
        rol_asignado = 'cliente'
        nuevo_usuario = Usuario(nombre=nombre, 
                                correo=correo, 
                                password=password_encriptada, 
                                rol=rol_asignado)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('¡Registro exitoso! Por favor inicia sesión.')
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            # return redirect(url_for('inventario'))
            # Redirección inteligente según el rol
            if usuario.rol == 'admin':
                return redirect(url_for('inventario'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos. Inténtalo de nuevo.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)