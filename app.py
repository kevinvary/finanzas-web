import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import sqlite3
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import csv
from datetime import datetime
from calendar import monthrange

from forms import AddCreatorForm, EditCreatorForm, AddEmployeeForm, EditEmployeeForm, AddTransactionForm, EditTransactionForm, AddPartnerForm, EditPartnerForm
from custom_widgets import CollapsibleMenu, CollapsibleFrame

class Theme:
    BACKGROUND = "#1a1a1e"; FRAME_COLOR = "#212126"; SIDEBAR_COLOR = "#1c1c21"
    WIDGET_COLOR = "#2b2b30"; TEXT_COLOR = "#e0e0e0"; ACCENT_COLOR = "#6a5acd"
    ACCENT_HOVER = "#5949a9"; GREEN = "#2E8B57"; RED = "#C70039"; BLUE = "#4a90e2"

ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
db_name = "db_ofmkevin.db"; icon_folder = "assets"
DASHBOARD_ICON = os.path.join(icon_folder, "dashboard.png"); CREATORS_ICON = os.path.join(icon_folder, "creators.png")
EMPLOYEES_ICON = os.path.join(icon_folder, "employees.png"); MANAGE_ICON = os.path.join(icon_folder, "manage.png")
FINANCES_ICON = os.path.join(icon_folder, "finances.png"); REPORTS_ICON = os.path.join(icon_folder, "reports.png")

def init_db():
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys=off;")
        cursor.execute("BEGIN TRANSACTION;")
        cursor.execute('''CREATE TABLE IF NOT EXISTS creadoras_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, sueldo_fijo REAL DEFAULT 0,
            porcentaje REAL DEFAULT 0, notas TEXT DEFAULT '', inversion REAL DEFAULT 0)''')
        try:
            cursor.execute("INSERT INTO creadoras_new (id, nombre, sueldo_fijo, porcentaje, notas, inversion) SELECT id, nombre, sueldo_fijo, porcentaje, notas, inversion FROM creadoras")
            cursor.execute("DROP TABLE creadoras")
            cursor.execute("ALTER TABLE creadoras_new RENAME TO creadoras")
        except sqlite3.OperationalError:
            cursor.execute("DROP TABLE IF EXISTS creadoras_new")
            cursor.execute('''CREATE TABLE IF NOT EXISTS creadoras (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, sueldo_fijo REAL DEFAULT 0,
                porcentaje REAL DEFAULT 0, notas TEXT DEFAULT '', inversion REAL DEFAULT 0)''')
        cursor.execute("COMMIT;")
        cursor.execute("PRAGMA foreign_keys=on;")
        try:
            cursor.execute('ALTER TABLE finanzas ADD COLUMN creadora_id INTEGER REFERENCES creadoras(id) ON DELETE SET NULL')
        except sqlite3.OperationalError: pass
        cursor.execute('''CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, rol TEXT, sueldo REAL DEFAULT 0,
            ventas REAL DEFAULT 0, comision REAL DEFAULT 0, notas TEXT DEFAULT '')''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS finanzas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL, categoria TEXT, monto REAL DEFAULT 0,
            descripcion TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            creadora_id INTEGER, FOREIGN KEY (creadora_id) REFERENCES creadoras (id) ON DELETE SET NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS categorias_finanzas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE)''')
        default_categories = ["Inversion App", "Servidor Virtual", "Marketing", "Inversion Creadora", "Ingreso General", "Comisión Retiro Cripto", "Sueldo", "Otro"]
        for cat in default_categories:
            cursor.execute("INSERT OR IGNORE INTO categorias_finanzas (nombre) VALUES (?)", (cat,))
        
        # --- NUEVAS TABLAS Y ALTERACIONES PARA SOCIOS ---
        cursor.execute('''CREATE TABLE IF NOT EXISTS socios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE, notas TEXT DEFAULT '')''')
        try:
            cursor.execute('ALTER TABLE creadoras ADD COLUMN socio_id INTEGER REFERENCES socios(id) ON DELETE SET NULL')
        except sqlite3.OperationalError: pass
        try:
            cursor.execute('ALTER TABLE empleados ADD COLUMN socio_id INTEGER REFERENCES socios(id) ON DELETE SET NULL')
        except sqlite3.OperationalError: pass


def get_db_data(query, params=()):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def get_current_month_income():
    query = "SELECT SUM(monto) FROM finanzas WHERE tipo='ingreso' AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now', 'localtime')"
    result = get_db_data(query)
    return result[0][0] or 0.0

def get_expense_breakdown():
    query_sueldos_c = "SELECT SUM(sueldo_fijo) FROM creadoras"
    query_sueldos_e = "SELECT SUM(sueldo) FROM empleados"
    query_comisiones_creadoras = """
        SELECT SUM(f.monto * c.porcentaje / 100) FROM finanzas f JOIN creadoras c ON f.creadora_id = c.id
        WHERE f.tipo = 'ingreso' AND c.porcentaje > 0"""
    query_comisiones_retiro = "SELECT SUM(monto) FROM finanzas WHERE categoria='Comisión Retiro Cripto'"
    query_inversiones = "SELECT SUM(inversion) FROM creadoras"
    query_otros_egresos = "SELECT SUM(monto) FROM finanzas WHERE tipo='egreso' AND categoria NOT IN ('Comisión Retiro Cripto', 'Sueldo', 'Inversion Creadora')"
    
    sueldos_creadoras = (get_db_data(query_sueldos_c)[0][0] or 0)
    sueldos_empleados = (get_db_data(query_sueldos_e)[0][0] or 0)
    comisiones_creadoras = (get_db_data(query_comisiones_creadoras)[0][0] or 0)
    comisiones_retiro = (get_db_data(query_comisiones_retiro)[0][0] or 0)
    inversiones = (get_db_data(query_inversiones)[0][0] or 0)
    otros_egresos = (get_db_data(query_otros_egresos)[0][0] or 0)
    
    return {"Sueldos": sueldos_creadoras + sueldos_empleados, "Comisión Creadoras": comisiones_creadoras,
            "Comisión Retiros": comisiones_retiro, "Inversiones": inversiones, "Otros Egresos": otros_egresos}

def get_top_creators_by_revenue(limit=5):
    query = """SELECT c.nombre, SUM(f.monto) FROM creadoras c JOIN finanzas f ON c.id = f.creadora_id
               WHERE f.tipo = 'ingreso' GROUP BY c.id ORDER BY SUM(f.monto) DESC LIMIT ?"""
    return get_db_data(query, (limit,))

def get_top_creators_by_profitability(limit=5):
    query = """SELECT c.nombre, SUM(CASE WHEN f.tipo = 'ingreso' THEN f.monto ELSE 0 END) - c.sueldo_fijo -
               (SUM(CASE WHEN f.tipo = 'ingreso' THEN f.monto ELSE 0 END) * c.porcentaje / 100) - c.inversion as profit
               FROM creadoras c LEFT JOIN finanzas f ON c.id = f.creadora_id
               GROUP BY c.id HAVING profit > 0 ORDER BY profit DESC LIMIT ?"""
    return get_db_data(query, (limit,))

def get_expense_by_category(limit=10):
    query = """
        SELECT categoria, SUM(monto) as total
        FROM finanzas
        WHERE tipo = 'egreso'
        GROUP BY categoria
        ORDER BY total DESC
        LIMIT ?
    """
    return get_db_data(query, (limit,))

def get_monthly_financial_trend(start_date=None, end_date=None):
    query = "SELECT strftime('%Y-%m', fecha) as mes, SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) as ingresos, SUM(CASE WHEN tipo = 'egreso' THEN monto ELSE 0 END) as egresos FROM finanzas "
    params = []
    conditions = []
    if start_date:
        conditions.append("date(fecha) >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date(fecha) <= ?")
        params.append(end_date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY mes ORDER BY mes ASC"
    data = get_db_data(query, tuple(params))
    return {"months": [row[0] for row in data], "incomes": [row[1] for row in data], "expenses": [row[2] for row in data]}

def get_distinct_months():
    """Obtiene una lista de meses únicos (YYYY-MM) de la base de datos."""
    query = "SELECT DISTINCT strftime('%Y-%m', fecha) as mes FROM finanzas ORDER BY mes DESC"
    data = get_db_data(query)
    return [row[0] for row in data]

def get_financial_data_by_date(start_date, end_date):
    query = """SELECT f.id, f.tipo, f.categoria, f.monto, f.descripcion, STRFTIME('%Y-%m-%d %H:%M', f.fecha), c.nombre
               FROM finanzas f LEFT JOIN creadoras c ON f.creadora_id = c.id
               WHERE date(f.fecha) BETWEEN ? AND ? ORDER BY f.fecha DESC"""
    return get_db_data(query, (start_date, end_date))

# --- NUEVA FUNCIÓN PARA GASTOS DE SOCIOS ---
def get_partner_expenses():
    partners = get_db_data("SELECT id, nombre FROM socios")
    partner_expenses = []

    for partner_id, partner_name in partners:
        q_creator_salaries = "SELECT IFNULL(SUM(sueldo_fijo), 0) FROM creadoras WHERE socio_id = ?"
        creator_salaries = get_db_data(q_creator_salaries, (partner_id,))[0][0]
        
        q_employee_salaries = "SELECT IFNULL(SUM(sueldo), 0) FROM empleados WHERE socio_id = ?"
        employee_salaries = get_db_data(q_employee_salaries, (partner_id,))[0][0]
        
        q_creator_commissions = """
            SELECT IFNULL(SUM(f.monto * c.porcentaje / 100), 0)
            FROM finanzas f JOIN creadoras c ON f.creadora_id = c.id
            WHERE f.tipo = 'ingreso' AND c.porcentaje > 0 AND c.socio_id = ?"""
        creator_commissions = get_db_data(q_creator_commissions, (partner_id,))[0][0]
        
        total_expense = creator_salaries + employee_salaries + creator_commissions
        if total_expense > 0:
            partner_expenses.append((partner_name, total_expense))
            
    return sorted(partner_expenses, key=lambda x: x[1], reverse=True)

def create_main_kpi_card(parent, title, value):
    frame = ctk.CTkFrame(parent, corner_radius=15, fg_color=Theme.FRAME_COLOR)
    ctk.CTkLabel(frame, text=title, font=("Arial", 20, "bold"), text_color="#a0a0a0").pack(anchor='n', padx=20, pady=(15, 5))
    ctk.CTkLabel(frame, text=f"${value:,.2f}", font=("Arial", 48, "bold"), text_color=Theme.GREEN).pack(anchor='n', padx=20, pady=(0, 20))
    return frame

def create_kpi_card(parent, title, value, value_color=None):
    frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=Theme.FRAME_COLOR)
    ctk.CTkLabel(frame, text=title, font=("Arial", 14), text_color="#a0a0a0").pack(anchor='nw', padx=15, pady=(8, 0))
    label_value = ctk.CTkLabel(frame, text=f"${value:.2f}", font=("Arial", 22, "bold"))
    if value_color: label_value.configure(text_color=value_color)
    label_value.pack(anchor='nw', padx=15, pady=(0, 8))
    return frame

def create_horizontal_bar_chart(parent, data, title, color):
    container_frame = ctk.CTkFrame(parent, fg_color="transparent")
    container_frame.pack(fill="both", expand=True)
    
    title_label = ctk.CTkLabel(container_frame, text=title, font=("Arial", 18, "bold"), anchor="w")
    title_label.pack(fill="x", padx=15, pady=(10, 5))

    chart_container = ctk.CTkFrame(container_frame, fg_color=Theme.FRAME_COLOR, corner_radius=10)
    chart_container.pack(fill="both", expand=True)

    if not data:
        ctk.CTkLabel(chart_container, text="No hay datos para mostrar.", font=("Arial", 16)).pack(expand=True, pady=20)
        return container_frame

    labels = [row[0] for row in data]; values = [row[1] for row in data]
    labels.reverse(); values.reverse()
    
    fig, ax = plt.subplots(figsize=(5, len(labels) * 0.6), dpi=100) # Altura dinámica
    fig.patch.set_facecolor(Theme.FRAME_COLOR); ax.set_facecolor(Theme.FRAME_COLOR)
    
    bars = ax.barh(labels, values, color=color, height=0.6)
    ax.tick_params(axis='x', colors=Theme.TEXT_COLOR); ax.tick_params(axis='y', colors=Theme.TEXT_COLOR, labelsize=12)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(Theme.FRAME_COLOR); ax.spines['bottom'].set_color(Theme.TEXT_COLOR)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: f'${x/1000:.1f}K' if x >= 1000 else f'${x:.0f}'))
    
    for bar in bars:
        width = bar.get_width()
        label_x_pos = width + max(values) * 0.02 if values else 0
        ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, f' ${width:,.2f}', va='center', color=Theme.TEXT_COLOR, fontsize=11)
        
    fig.tight_layout(pad=2)
    canvas = FigureCanvasTkAgg(fig, master=chart_container); canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)
    
    return container_frame

def create_styled_view(root, title, columns):
    for widget in root.winfo_children(): widget.destroy()
    root.configure(fg_color=Theme.BACKGROUND)
    style = ttk.Style(); style.theme_use("default")
    style.configure("Treeview", background=Theme.FRAME_COLOR, foreground=Theme.TEXT_COLOR, fieldbackground=Theme.FRAME_COLOR, borderwidth=0, rowheight=35)
    style.map("Treeview", background=[('selected', Theme.ACCENT_COLOR)])
    style.configure("Treeview.Heading", background=Theme.WIDGET_COLOR, foreground=Theme.TEXT_COLOR, font=("Arial", 14, "bold"), borderwidth=0)
    container = ctk.CTkFrame(root, fg_color="transparent"); container.pack(fill='both', expand=True, padx=30, pady=20)
    top_frame = ctk.CTkFrame(container, fg_color="transparent"); top_frame.pack(fill='x', pady=(0, 20))
    ctk.CTkLabel(top_frame, text=title, font=("Arial", 32, "bold")).pack(side="left")
    buttons_frame = ctk.CTkFrame(top_frame, fg_color="transparent"); buttons_frame.pack(side="right")
    tree = ttk.Treeview(container, columns=columns, show='headings'); tree.pack(fill='both', expand=True)
    for col_name in columns: tree.heading(col_name, text=col_name)
    return container, buttons_frame, tree

def mostrar_dashboard(root):
    for widget in root.winfo_children(): widget.destroy()
    root.configure(fg_color=Theme.BACKGROUND)

    scroll_frame = ctk.CTkScrollableFrame(root, fg_color="transparent", scrollbar_button_color=Theme.WIDGET_COLOR, scrollbar_button_hover_color=Theme.ACCENT_HOVER)
    scroll_frame.pack(fill="both", expand=True)
    scroll_frame.grid_columnconfigure(0, weight=1) 

    content_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
    content_frame.pack(fill="x", expand=True, padx=20, pady=15)
    
    ctk.CTkLabel(content_frame, text="Dashboard de Análisis", font=("Arial", 32, "bold")).pack(anchor="w", padx=10, pady=10)

    main_kpi_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    main_kpi_frame.pack(fill="x", pady=(0, 10))
    main_kpi_frame.grid_columnconfigure(0, weight=1)
    ingresos_mes = get_current_month_income()
    create_main_kpi_card(main_kpi_frame, "Ingresos Totales del Mes", ingresos_mes).grid(row=0, column=0, sticky="ew", padx=10)

    ctk.CTkLabel(content_frame, text="Resumen de Gastos", font=("Arial", 18, "bold"), text_color="#a0a0a0").pack(anchor="w", padx=10, pady=(10,5))

    kpi_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    kpi_frame.pack(fill="x", pady=5)
    kpi_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
    expense_data = get_expense_breakdown()
    create_kpi_card(kpi_frame, "Sueldos", expense_data["Sueldos"]).grid(row=0, column=0, padx=10, sticky="ew")
    create_kpi_card(kpi_frame, "Comisión Creadoras", expense_data["Comisión Creadoras"]).grid(row=0, column=1, padx=10, sticky="ew")
    create_kpi_card(kpi_frame, "Comisión Retiros", expense_data["Comisión Retiros"], value_color=Theme.RED).grid(row=0, column=2, padx=10, sticky="ew")
    create_kpi_card(kpi_frame, "Inversiones", expense_data["Inversiones"]).grid(row=0, column=3, padx=10, sticky="ew")
    create_kpi_card(kpi_frame, "Otros Egresos", expense_data["Otros Egresos"]).grid(row=0, column=4, padx=10, sticky="ew")

    charts_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    charts_frame.pack(fill="x", expand=True, pady=10)
    charts_frame.grid_columnconfigure(0, weight=2); charts_frame.grid_columnconfigure(1, weight=3)
    charts_frame.grid_rowconfigure(0, weight=1)

    # --- Columna Izquierda ---
    left_column_frame = ctk.CTkFrame(charts_frame, fg_color="transparent")
    left_column_frame.grid(row=0, column=0, padx=(0, 10), sticky="new")
    left_column_frame.grid_columnconfigure(0, weight=1)

    pie_chart_frame = ctk.CTkFrame(left_column_frame, corner_radius=10, fg_color=Theme.FRAME_COLOR)
    pie_chart_frame.grid(row=0, column=0, sticky="new", pady=(0, 10))
    ctk.CTkLabel(pie_chart_frame, text="Desglose General de Gastos", font=("Arial", 18, "bold")).pack(anchor="w", padx=15, pady=(10,5))
    pie_labels = [label for label, value in expense_data.items() if value > 0]
    pie_values = [value for value in expense_data.values() if value > 0]
    if not pie_values: ctk.CTkLabel(pie_chart_frame, text="No hay datos de gastos.", font=("Arial", 16)).pack(expand=True)
    else:
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100); fig.patch.set_facecolor(Theme.FRAME_COLOR)
        wedge_properties = {'width': 0.4, 'edgecolor': Theme.FRAME_COLOR, 'linewidth': 2}
        colors = plt.cm.viridis(np.linspace(0, 1, len(pie_labels)))
        wedges, texts, autotexts = ax.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=140, pctdistance=0.8, colors=colors, wedgeprops=wedge_properties, textprops={'color': Theme.TEXT_COLOR, 'fontsize': 12})
        for autotext in autotexts: autotext.set_color("white"); autotext.set_fontweight('bold')
        canvas = FigureCanvasTkAgg(fig, master=pie_chart_frame); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    
    collapsible_expenses = CollapsibleFrame(left_column_frame, title="Ver Desglose de Gastos")
    collapsible_expenses.grid(row=1, column=0, sticky="new", pady=(10,0))
    expense_category_data = get_expense_by_category()
    create_horizontal_bar_chart(
        parent=collapsible_expenses.content_frame, data=expense_category_data,
        title="Gastos por Categoría", color=Theme.RED)
    
    # --- NUEVO GRÁFICO DE GASTOS POR SOCIO ---
    collapsible_partners = CollapsibleFrame(left_column_frame, title="Ver Gastos por Socio")
    collapsible_partners.grid(row=2, column=0, sticky="new", pady=(10,0))
    partner_expense_data = get_partner_expenses()
    create_horizontal_bar_chart(
        parent=collapsible_partners.content_frame, data=partner_expense_data,
        title="Gastos Totales por Socio", color=Theme.BLUE)

    # --- Columna Derecha ---
    right_column_frame = ctk.CTkFrame(charts_frame, fg_color="transparent")
    right_column_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
    right_column_frame.grid_rowconfigure(0, weight=1); right_column_frame.grid_rowconfigure(1, weight=1)
    right_column_frame.grid_columnconfigure(0, weight=1)
    
    revenue_chart_parent = ctk.CTkFrame(right_column_frame, fg_color="transparent")
    revenue_chart_parent.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
    create_horizontal_bar_chart(revenue_chart_parent, get_top_creators_by_revenue(), "Top Creadoras por Ingresos", Theme.GREEN)
    
    profit_chart_parent = ctk.CTkFrame(right_column_frame, fg_color="transparent")
    profit_chart_parent.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    create_horizontal_bar_chart(profit_chart_parent, get_top_creators_by_profitability(), "Top Creadoras por Rentabilidad", Theme.ACCENT_COLOR)

def mostrar_creadoras(root):
    container, buttons_frame, tree = create_styled_view(root, "Manage Creators", ("ID", "Nombre", "Ingresos Totales", "Sueldo Fijo", "%", "Inversión", "Socio"))
    tree.column("ID", width=40, anchor='center'); tree.column("Ingresos Totales", width=120, anchor='e'); tree.column("Sueldo Fijo", width=120, anchor='e'); tree.column("%", width=60, anchor='e'); tree.column("Inversión", width=120, anchor='e'); tree.column("Socio", width=120, anchor='center')
    add_button = ctk.CTkButton(buttons_frame, text="Add Creator", fg_color=Theme.ACCENT_COLOR, hover_color=Theme.ACCENT_HOVER, command=lambda: AddCreatorForm(root, db_name, lambda: mostrar_creadoras(root))); add_button.pack(side="left", padx=5)
    edit_button = ctk.CTkButton(buttons_frame, text="Edit", state="disabled"); edit_button.pack(side="left", padx=5)
    delete_button = ctk.CTkButton(buttons_frame, text="Delete", state="disabled", fg_color="#D2691E"); delete_button.pack(side="left", padx=5)
    def on_select(event): edit_button.configure(state="normal"); delete_button.configure(state="normal")
    tree.bind("<<TreeviewSelect>>", on_select)
    def get_selected_creator():
        if not tree.selection(): return None
        item_id = tree.item(tree.selection()[0])['values'][0]
        data_rows = get_db_data("SELECT id, nombre, sueldo_fijo, porcentaje, notas, inversion, socio_id FROM creadoras WHERE id=?", (item_id,))
        if not data_rows: return None
        data = data_rows[0]
        return {'id': data[0], 'nombre': data[1], 'sueldo_fijo': data[2], 'porcentaje': data[3], 'notas': data[4], 'inversion': data[5], 'socio_id': data[6]}
    def open_edit_form():
        creator_data = get_selected_creator()
        if creator_data: EditCreatorForm(root, db_name, lambda: mostrar_creadoras(root), creator_data)
    def delete_item():
        creator_data = get_selected_creator()
        if creator_data and messagebox.askyesno("Confirmar", f"¿Eliminar a {creator_data['nombre']}?\n¡Todas sus transacciones financieras asociadas serán desvinculadas, pero no eliminadas!", icon=messagebox.WARNING):
            with sqlite3.connect(db_name) as conn: conn.execute("DELETE FROM creadoras WHERE id=?", (creator_data['id'],))
            mostrar_creadoras(root)
    edit_button.configure(command=open_edit_form); delete_button.configure(command=delete_item)
    query = """
        SELECT c.id, c.nombre, IFNULL(SUM(f.monto), 0) as total_ingresos, c.sueldo_fijo, c.porcentaje, c.inversion, s.nombre
        FROM creadoras c 
        LEFT JOIN finanzas f ON c.id = f.creadora_id AND f.tipo = 'ingreso'
        LEFT JOIN socios s ON c.socio_id = s.id
        GROUP BY c.id, c.nombre ORDER BY c.nombre"""
    for row in tree.get_children(): tree.delete(row)
    for row in get_db_data(query):
        formatted_row = list(row); formatted_row[2] = f"${row[2]:.2f}"; formatted_row[3] = f"${row[3]:.2f}"
        formatted_row[4] = f"{row[4]:.1f}%"; formatted_row[5] = f"${row[5]:.2f}"
        if formatted_row[6] is None: formatted_row[6] = "N/A"
        tree.insert("", tk.END, values=formatted_row)

def mostrar_empleados(root):
    container, buttons_frame, tree = create_styled_view(root, "Manage Employees", ("ID", "Nombre", "Rol", "Sueldo", "Ventas", "Comisión", "Socio"))
    tree.column("ID", width=40, anchor='center'); tree.column("Sueldo", width=100, anchor='e'); tree.column("Ventas", width=100, anchor='e'); tree.column("Comisión", width=100, anchor='e'); tree.column("Socio", width=120, anchor='center')
    add_button = ctk.CTkButton(buttons_frame, text="Add Employee", fg_color=Theme.ACCENT_COLOR, hover_color=Theme.ACCENT_HOVER, command=lambda: AddEmployeeForm(root, db_name, lambda: mostrar_empleados(root))); add_button.pack(side="left", padx=5)
    edit_button = ctk.CTkButton(buttons_frame, text="Edit", state="disabled"); edit_button.pack(side="left", padx=5)
    delete_button = ctk.CTkButton(buttons_frame, text="Delete", state="disabled", fg_color="#D2691E"); delete_button.pack(side="left", padx=5)
    def on_select(event): edit_button.configure(state="normal"); delete_button.configure(state="normal")
    tree.bind("<<TreeviewSelect>>", on_select)
    def get_selected_employee():
        if not tree.selection(): messagebox.showwarning("Sin selección", "Por favor, selecciona un empleado."); return None
        item_id = tree.item(tree.selection()[0])['values'][0]
        data = get_db_data("SELECT * FROM empleados WHERE id=?", (item_id,))
        if not data: return None
        data_row = data[0]
        return {'id': data_row[0], 'nombre': data_row[1], 'rol': data_row[2], 'sueldo': data_row[3], 'ventas': data_row[4], 'comision': data_row[5], 'notas': data_row[6], 'socio_id': data_row[7]}
    def open_edit_form():
        employee_data = get_selected_employee()
        if employee_data:
            EditEmployeeForm(root, db_name, lambda: mostrar_empleados(root), employee_data)
    def delete_item():
        employee_data = get_selected_employee()
        if employee_data and messagebox.askyesno("Confirmar", f"¿Eliminar empleado '{employee_data['nombre']}'?"):
            with sqlite3.connect(db_name) as conn: conn.execute("DELETE FROM empleados WHERE id=?", (employee_data['id'],))
            mostrar_empleados(root)
    edit_button.configure(command=open_edit_form); delete_button.configure(command=delete_item)
    for row in tree.get_children(): tree.delete(row)
    query = """
        SELECT e.id, e.nombre, e.rol, e.sueldo, e.ventas, e.comision, s.nombre
        FROM empleados e
        LEFT JOIN socios s ON e.socio_id = s.id
        ORDER BY e.nombre"""
    for row in get_db_data(query):
        formatted_row = list(row); formatted_row[3] = f"${row[3]:.2f}"; formatted_row[4] = f"${row[4]:.2f}"; formatted_row[5] = f"{row[5]:.1f}%"
        if formatted_row[6] is None: formatted_row[6] = "N/A"
        tree.insert("", tk.END, values=formatted_row)

# --- NUEVA VISTA PARA SOCIOS ---
def mostrar_socios(root):
    container, buttons_frame, tree = create_styled_view(root, "Manage Partners", ("ID", "Nombre", "Creadoras", "Empleados", "Notas"))
    tree.column("ID", width=40, anchor='center'); tree.column("Creadoras", width=120, anchor='center'); tree.column("Empleados", width=120, anchor='center')
    
    add_button = ctk.CTkButton(buttons_frame, text="Add Partner", fg_color=Theme.ACCENT_COLOR, hover_color=Theme.ACCENT_HOVER, command=lambda: AddPartnerForm(root, db_name, lambda: mostrar_socios(root)))
    add_button.pack(side="left", padx=5)
    edit_button = ctk.CTkButton(buttons_frame, text="Edit", state="disabled")
    edit_button.pack(side="left", padx=5)
    delete_button = ctk.CTkButton(buttons_frame, text="Delete", state="disabled", fg_color="#D2691E")
    delete_button.pack(side="left", padx=5)
    
    def on_select(event): edit_button.configure(state="normal"); delete_button.configure(state="normal")
    tree.bind("<<TreeviewSelect>>", on_select)
    
    def get_selected_partner():
        if not tree.selection(): return None
        item_id = tree.item(tree.selection()[0])['values'][0]
        data = get_db_data("SELECT * FROM socios WHERE id=?", (item_id,))
        if not data: return None
        return {'id': data[0][0], 'nombre': data[0][1], 'notas': data[0][2]}

    def open_edit_form():
        partner_data = get_selected_partner()
        if partner_data: EditPartnerForm(root, db_name, lambda: mostrar_socios(root), partner_data)

    def delete_item():
        partner_data = get_selected_partner()
        if partner_data and messagebox.askyesno("Confirmar", f"¿Eliminar al socio '{partner_data['nombre']}'?\n\nEsto desasignará a todas las creadoras y empleados asociados, pero no los eliminará a ellos.", icon=messagebox.WARNING):
            with sqlite3.connect(db_name) as conn: conn.execute("DELETE FROM socios WHERE id=?", (partner_data['id'],))
            mostrar_socios(root)

    edit_button.configure(command=open_edit_form)
    delete_button.configure(command=delete_item)

    for row in tree.get_children(): tree.delete(row)
    query = """
        SELECT s.id, s.nombre,
               (SELECT COUNT(c.id) FROM creadoras c WHERE c.socio_id = s.id),
               (SELECT COUNT(e.id) FROM empleados e WHERE e.socio_id = s.id),
               s.notas
        FROM socios s ORDER BY s.nombre"""
    for row in get_db_data(query): tree.insert("", tk.END, values=row)

def mostrar_finanzas(root):
    container, buttons_frame, tree = create_styled_view(root, "Manage Finances", ("ID", "Tipo", "Categoría", "Monto", "Asociado a", "Descripción", "Fecha"))
    tree.column("Asociado a", width=120, anchor='center')
    tree.tag_configure('ingreso', foreground=Theme.GREEN); tree.tag_configure('egreso', foreground=Theme.RED)
    add_button = ctk.CTkButton(buttons_frame, text="Add Transaction", fg_color=Theme.ACCENT_COLOR, hover_color=Theme.ACCENT_HOVER, command=lambda: AddTransactionForm(root, db_name, lambda: mostrar_finanzas(root)))
    add_button.pack(side="left", padx=5)
    edit_button = ctk.CTkButton(buttons_frame, text="Edit", state="disabled"); edit_button.pack(side="left", padx=5)
    delete_button = ctk.CTkButton(buttons_frame, text="Delete", state="disabled", fg_color="#D2691E"); delete_button.pack(side="left", padx=5)
    def on_select(event): edit_button.configure(state="normal"); delete_button.configure(state="normal")
    tree.bind("<<TreeviewSelect>>", on_select)
    def get_selected_transaction():
        if not tree.selection(): return None
        item_id = tree.item(tree.selection()[0])['values'][0]
        data = get_db_data("SELECT * FROM finanzas WHERE id=?", (item_id,))
        if not data: return None
        data_row = data[0]
        return {'id': data_row[0], 'tipo': data_row[1], 'categoria': data_row[2], 'monto': data_row[3], 'descripcion': data_row[4], 'fecha': data_row[5], 'creadora_id': data_row[6]}
    def open_edit_form():
        transaction_data = get_selected_transaction()
        if transaction_data: EditTransactionForm(root, db_name, lambda: mostrar_finanzas(root), transaction_data)
    def delete_item():
        transaction_data = get_selected_transaction()
        if transaction_data and messagebox.askyesno("Confirmar", f"¿Eliminar transacción con ID {transaction_data['id']}?", icon=messagebox.WARNING):
            with sqlite3.connect(db_name) as conn: conn.execute("DELETE FROM finanzas WHERE id=?", (transaction_data['id'],))
            mostrar_finanzas(root)
    edit_button.configure(command=open_edit_form); delete_button.configure(command=delete_item)
    query = """SELECT f.id, f.tipo, f.categoria, f.monto, c.nombre, f.descripcion, STRFTIME('%Y-%m-%d %H:%M', f.fecha)
               FROM finanzas f LEFT JOIN creadoras c ON f.creadora_id = c.id ORDER BY f.fecha DESC"""
    for row in tree.get_children(): tree.delete(row)
    for row in get_db_data(query):
        tags = (row[1],); formatted_row = list(row); formatted_row[3] = f"${row[3]:.2f}"
        if formatted_row[4] is None: formatted_row[4] = "N/A"
        tree.insert("", tk.END, values=formatted_row, tags=tags)

def mostrar_reportes(root):
    for widget in root.winfo_children(): widget.destroy()
    root.configure(fg_color=Theme.BACKGROUND)

    style = ttk.Style(); style.theme_use("default")
    style.configure("Treeview", background=Theme.FRAME_COLOR, foreground=Theme.TEXT_COLOR, fieldbackground=Theme.FRAME_COLOR, borderwidth=0, rowheight=35)
    style.map("Treeview", background=[('selected', Theme.ACCENT_COLOR)])
    style.configure("Treeview.Heading", background=Theme.WIDGET_COLOR, foreground=Theme.TEXT_COLOR, font=("Arial", 14, "bold"), borderwidth=0)
    
    container = ctk.CTkFrame(root, fg_color="transparent")
    container.pack(fill='both', expand=True, padx=30, pady=20)
    
    top_frame = ctk.CTkFrame(container, fg_color="transparent")
    top_frame.pack(fill='x', pady=(0, 10))
    ctk.CTkLabel(top_frame, text="Reporte Financiero Mensual", font=("Arial", 32, "bold")).pack(side="left")
    export_button = ctk.CTkButton(top_frame, text="Exportar a CSV", fg_color=Theme.ACCENT_COLOR, hover_color=Theme.ACCENT_HOVER)
    export_button.pack(side="right", padx=5)

    filter_frame = ctk.CTkFrame(container, fg_color=Theme.FRAME_COLOR, corner_radius=10)
    filter_frame.pack(fill='x', pady=10)
    
    ctk.CTkLabel(filter_frame, text="Seleccionar Mes:", font=("Arial", 14, "bold")).pack(side="left", padx=(15, 5), pady=10)
    months = ["Todos los Meses"] + get_distinct_months()
    month_combo = ctk.CTkComboBox(filter_frame, values=months, width=150)
    month_combo.pack(side="left", padx=5, pady=10)
    
    ctk.CTkLabel(filter_frame, text="o Rango Manual:", font=("Arial", 14)).pack(side="left", padx=(15, 5), pady=10)
    start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
    start_date_entry.pack(side="left", padx=5, pady=10)
    end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
    end_date_entry.pack(side="left", padx=5, pady=10)
    filter_button = ctk.CTkButton(filter_frame, text="Filtrar")
    filter_button.pack(side="left", padx=5, pady=10)
    reset_button = ctk.CTkButton(filter_frame, text="Limpiar", fg_color=Theme.WIDGET_COLOR)
    reset_button.pack(side="left", padx=5, pady=10)

    columns = ("Mes", "Ingresos", "Egresos", "Beneficio")
    tree = ttk.Treeview(container, columns=columns, show='headings')
    tree.pack(fill='both', expand=True, pady=(10, 0))
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='e', width=150)
    tree.column("Mes", anchor='center')
    
    tree.tag_configure('ganancia', foreground=Theme.GREEN)
    tree.tag_configure('perdida', foreground=Theme.RED)

    def populate_report(start_date=None, end_date=None):
        for row in tree.get_children():
            tree.delete(row)
        
        financial_data = get_monthly_financial_trend(start_date, end_date)
        
        for i, month in enumerate(financial_data["months"]):
            income = financial_data["incomes"][i]
            expense = financial_data["expenses"][i]
            profit = income - expense
            tag = 'ganancia' if profit >= 0 else 'perdida'
            formatted_row = (month, f"${income:,.2f}", f"${expense:,.2f}", f"${profit:,.2f}")
            tree.insert("", tk.END, values=formatted_row, tags=(tag,))

    def apply_filter():
        start = start_date_entry.get()
        end = end_date_entry.get()
        try:
            if start: datetime.strptime(start, '%Y-%m-%d')
            if end: datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error de Formato", "Por favor, usa el formato YYYY-MM-DD para las fechas.", parent=root)
            return
        month_combo.set("Todos los Meses")
        populate_report(start_date=start or None, end_date=end or None)
        
    def clear_filter():
        start_date_entry.delete(0, 'end')
        end_date_entry.delete(0, 'end')
        month_combo.set("Todos los Meses")
        populate_report()

    def on_month_select(selected_month):
        if selected_month == "Todos los Meses":
            clear_filter()
            return
        
        try:
            year, month = map(int, selected_month.split('-'))
            start_date = f"{selected_month}-01"
            last_day = monthrange(year, month)[1]
            end_date = f"{selected_month}-{last_day}"
            
            start_date_entry.delete(0, 'end'); start_date_entry.insert(0, start_date)
            end_date_entry.delete(0, 'end'); end_date_entry.insert(0, end_date)
            populate_report(start_date, end_date)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo procesar el mes seleccionado: {e}", parent=root)

    def export_to_csv():
        if not tree.get_children():
            messagebox.showwarning("Sin Datos", "No hay datos para exportar.", parent=root)
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], title="Guardar Reporte Como...")
        if not filepath: return
            
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for child in tree.get_children():
                    writer.writerow(tree.item(child)['values'])
            messagebox.showinfo("Éxito", f"Reporte guardado exitosamente en:\n{filepath}", parent=root)
        except IOError as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar el archivo:\n{e}", parent=root)

    filter_button.configure(command=apply_filter)
    reset_button.configure(command=clear_filter)
    export_button.configure(command=export_to_csv)
    month_combo.configure(command=on_month_select)

    populate_report()

def main():
    init_db()
    app = ctk.CTk(); app.title("OFM KEVIN - Agency Manager"); app.geometry("1600x900")
    app.grid_columnconfigure(1, weight=1); app.grid_rowconfigure(0, weight=1)
    frame_sidebar = ctk.CTkFrame(app, width=280, fg_color=Theme.SIDEBAR_COLOR, corner_radius=0); frame_sidebar.grid(row=0, column=0, sticky="nsw")
    frame_main = ctk.CTkFrame(app, fg_color=Theme.BACKGROUND, corner_radius=0); frame_main.grid(row=0, column=1, sticky="nsew")
    ctk.CTkLabel(frame_sidebar, text="OFM KEVIN", font=("Arial", 24, "bold")).pack(pady=25, padx=20)
    
    dashboard_button = ctk.CTkButton(frame_sidebar, text="  Dashboard", anchor="w", fg_color="transparent", font=("Arial", 16, "bold"), command=lambda: mostrar_dashboard(frame_main))
    dashboard_button.pack(fill="x", padx=20, pady=5)
    reports_button = ctk.CTkButton(frame_sidebar, text="  Reportes", anchor="w", fg_color="transparent", font=("Arial", 16, "bold"), command=lambda: mostrar_reportes(frame_main))
    reports_button.pack(fill="x", padx=20, pady=5)

    ctk.CTkLabel(frame_sidebar, text="GESTIÓN", font=("Arial", 12, "bold"), text_color="#a0a0a0").pack(pady=(20, 5), padx=20, anchor="w")
    CollapsibleMenu(frame_sidebar, "Creators", CREATORS_ICON, [("Manage creators", MANAGE_ICON, lambda: mostrar_creadoras(frame_main))]).pack(fill="x", padx=10, pady=5)
    CollapsibleMenu(frame_sidebar, "Employees", EMPLOYEES_ICON, [("Manage employees", MANAGE_ICON, lambda: mostrar_empleados(frame_main))]).pack(fill="x", padx=10, pady=5)
    CollapsibleMenu(frame_sidebar, "Partners", EMPLOYEES_ICON, [("Manage partners", MANAGE_ICON, lambda: mostrar_socios(frame_main))]).pack(fill="x", padx=10, pady=5)
    CollapsibleMenu(frame_sidebar, "Finances", FINANCES_ICON, [("Transactions", MANAGE_ICON, lambda: mostrar_finanzas(frame_main))]).pack(fill="x", padx=10, pady=5)
    
    mostrar_dashboard(frame_main)
    app.mainloop()

if __name__ == "__main__":
    main()