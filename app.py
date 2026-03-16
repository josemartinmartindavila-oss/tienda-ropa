from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de la Base de Datos y la carpeta de imágenes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tienda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

# Crear carpeta de subidas si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Modelo (Tabla) para las Prendas según HU 10
class Prenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    talla = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(255), nullable=False)

# Crear la base de datos al iniciar
with app.app_context():
    db.create_all()

# Ruta 1: El Inicio (Index)
@app.route('/')
def index():
    return render_template('index.html')

# Ruta 2: HU 10 - Agregar Prenda
@app.route('/agregar', methods=['GET', 'POST'])
def agregar_prenda():
    if request.method == 'POST':
        # Capturar la imagen
        file = request.files['imagen']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = 'default.png'

        # Guardar en la base de datos
        nueva_prenda = Prenda(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            talla=request.form['talla'],
            color=request.form['color'],
            precio=float(request.form['precio']),
            imagen=filename
        )
        db.session.add(nueva_prenda)
        db.session.commit()

        # Por ahora, redirigir al inicio tras guardar
        return redirect(url_for('index'))

    return render_template('agregar.html')

if __name__ == '__main__':
    app.run(debug=True)