from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# Más rutas si las necesitás (ejemplo)
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Aquí podrías importar y usar tu lógica existente de forms.py o base de datos
# Ejemplo:
# from forms import get_financial_data
# @app.route('/data')
# def data():
#     return get_financial_data()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
