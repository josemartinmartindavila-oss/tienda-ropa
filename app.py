from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tienda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class Prenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    talla = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(30), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=1)
    imagen = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    prendas_guardadas = Prenda.query.all()
    return render_template('index.html', prendas=prendas_guardadas)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar_prenda():
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

@app.route('/prenda/<int:id>')
def detalle_prenda(id):
    prenda_seleccionada = Prenda.query.get_or_404(id)
    return render_template('detalle.html', prenda=prenda_seleccionada)

@app.route('/inventario')
def inventario():
    prendas_guardadas = Prenda.query.all()
    return render_template('inventario.html', prendas=prendas_guardadas)

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_prenda(id):
    prenda_a_eliminar = Prenda.query.get_or_404(id)
    db.session.delete(prenda_a_eliminar)
    db.session.commit()
    return redirect(url_for('inventario'))

# --- RUTA 6: HU 11 - Editar Prenda ---
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_prenda(id):
    # Buscamos la prenda actual
    prenda_a_editar = Prenda.query.get_or_404(id)

    if request.method == 'POST':
        # Sobrescribimos los datos con los nuevos del formulario
        prenda_a_editar.nombre = request.form['nombre']
        prenda_a_editar.descripcion = request.form['descripcion']
        prenda_a_editar.talla = request.form['talla']
        prenda_a_editar.color = request.form['color']
        prenda_a_editar.precio = float(request.form['precio'])
        prenda_a_editar.stock = int(request.form['stock'])

        # Solo guardamos imagen si el usuario subió una nueva
        file = request.files['imagen']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            prenda_a_editar.imagen = filename

        db.session.commit()
        return redirect(url_for('inventario'))

    return render_template('editar.html', prenda=prenda_a_editar)

if __name__ == '__main__':
    app.run(debug=True)