
from flask import Flask, render_template, request, redirect, url_for, flash
from forms import *
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'db_ofmkevin.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    # Cargar datos de ejemplo
    finances = conn.execute('SELECT * FROM finances').fetchall()
    conn.close()
    return render_template('dashboard.html', finances=finances)

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/manage/creators')
def manage_creators():
    return render_template('manage_creators.html')

@app.route('/manage/employees')
def manage_employees():
    return render_template('manage_employees.html')

@app.route('/manage/partners')
def manage_partners():
    return render_template('manage_partners.html')

@app.route('/finances')
def finances():
    conn = get_db_connection()
    finances = conn.execute('SELECT * FROM finances').fetchall()
    conn.close()
    return render_template('finances.html', finances=finances)

if __name__ == '__main__':
    app.run(debug=True)
