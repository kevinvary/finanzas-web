import customtkinter as ctk
import sqlite3
from tkinter import messagebox

class AddCreatorForm(ctk.CTkToplevel):
    def __init__(self, master, db_name, on_close_callback):
        super().__init__(master)
        self.db_name = db_name
        self.on_close_callback = on_close_callback
        self.title("Añadir Nueva Creadora")
        self.geometry("400x500")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text="Nombre:", font=("Arial", 14)).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.nombre_entry = ctk.CTkEntry(self, placeholder_text="Ej: Kate", width=200)
        self.nombre_entry.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Sueldo Fijo ($):", font=("Arial", 14)).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.sueldo_entry = ctk.CTkEntry(self, placeholder_text="Ej: 500.00")
        self.sueldo_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Porcentaje (%):", font=("Arial", 14)).grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.porcentaje_entry = ctk.CTkEntry(self, placeholder_text="Opcional. Ej: 15")
        self.porcentaje_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Inversión ($):", font=("Arial", 14)).grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.inversion_entry = ctk.CTkEntry(self, placeholder_text="Opcional. Ej: 100.00")
        self.inversion_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Notas:", font=("Arial", 14)).grid(row=4, column=0, padx=20, pady=10, sticky="nw")
        self.notas_textbox = ctk.CTkTextbox(self, height=100)
        self.notas_textbox.grid(row=4, column=1, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(self, text="Socio Asignado:", font=("Arial", 14)).grid(row=5, column=0, padx=20, pady=10, sticky="w")
        self.partner_combo = ctk.CTkComboBox(self, values=[])
        self.partner_combo.grid(row=5, column=1, padx=20, pady=10, sticky="ew")
        self.partners_map = self.load_partners()

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Guardar Creadora", command=self.save_creator).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancelar", command=self.on_window_close, fg_color="#555555").pack(side="left", padx=10)
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def load_partners(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre FROM socios ORDER BY nombre ASC")
                partners = cursor.fetchall()
            partners_map = {name: id for id, name in partners}
            partner_names = list(partners_map.keys())
            partner_names.insert(0, "Ninguno")
            partners_map["Ninguno"] = None
            self.partner_combo.configure(values=partner_names)
            self.partner_combo.set("Ninguno")
            return partners_map
        except sqlite3.Error as e:
            messagebox.showerror("Error en DB", f"No se pudieron cargar los socios: {e}", parent=self)
            return {"Ninguno": None}

    def on_window_close(self): self.on_close_callback(); self.destroy()

    def save_creator(self):
        nombre = self.nombre_entry.get().strip()
        sueldo_str = self.sueldo_entry.get().strip(); porcentaje_str = self.porcentaje_entry.get().strip()
        inversion_str = self.inversion_entry.get().strip(); notas = self.notas_textbox.get("1.0", "end-1c").strip()
        selected_partner_name = self.partner_combo.get()
        partner_id = self.partners_map.get(selected_partner_name)

        if not nombre: messagebox.showerror("Error de Validación", "El campo 'Nombre' no puede estar vacío.", parent=self); return
        try:
            sueldo = float(sueldo_str) if sueldo_str else 0.0
            porcentaje = float(porcentaje_str) if porcentaje_str else 0.0
            inversion = float(inversion_str) if inversion_str else 0.0
        except ValueError: messagebox.showerror("Error de Validación", "Los campos numéricos deben ser números válidos.", parent=self); return
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO creadoras (nombre, sueldo_fijo, porcentaje, inversion, notas, socio_id) VALUES (?, ?, ?, ?, ?, ?)', 
                               (nombre, sueldo, porcentaje, inversion, notas, partner_id))
            messagebox.showinfo("Éxito", f"Creadora '{nombre}' guardada correctamente.", parent=self); self.on_window_close()
        except sqlite3.Error as e: messagebox.showerror("Error en la Base de Datos", f"No se pudo guardar la creadora: {e}", parent=self)

class EditCreatorForm(AddCreatorForm):
    def __init__(self, master, db_name, on_close_callback, creator_data):
        super().__init__(master, db_name, on_close_callback)
        self.title("Editar Creadora"); self.creator_id = creator_data['id']
        self.nombre_entry.insert(0, creator_data['nombre'])
        self.sueldo_entry.insert(0, str(creator_data['sueldo_fijo']))
        self.porcentaje_entry.insert(0, str(creator_data['porcentaje']))
        self.inversion_entry.insert(0, str(creator_data['inversion']))
        self.notas_textbox.insert("1.0", creator_data['notas'])
        
        if creator_data.get('socio_id') is not None:
            partner_name = [name for name, id in self.partners_map.items() if id == creator_data.get('socio_id')]
            if partner_name:
                self.partner_combo.set(partner_name[0])

    def save_creator(self):
        nombre = self.nombre_entry.get().strip()
        sueldo_str = self.sueldo_entry.get().strip(); porcentaje_str = self.porcentaje_entry.get().strip()
        inversion_str = self.inversion_entry.get().strip(); notas = self.notas_textbox.get("1.0", "end-1c").strip()
        selected_partner_name = self.partner_combo.get()
        partner_id = self.partners_map.get(selected_partner_name)

        if not nombre: messagebox.showerror("Error de Validación", "El campo 'Nombre' no puede estar vacío.", parent=self); return
        try:
            sueldo = float(sueldo_str) if sueldo_str else 0.0
            porcentaje = float(porcentaje_str) if porcentaje_str else 0.0
            inversion = float(inversion_str) if inversion_str else 0.0
        except ValueError: messagebox.showerror("Error de Validación", "Los campos numéricos deben ser números válidos.", parent=self); return
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE creadoras SET nombre=?, sueldo_fijo=?, porcentaje=?, inversion=?, notas=?, socio_id=? WHERE id=?', 
                               (nombre, sueldo, porcentaje, inversion, notas, partner_id, self.creator_id))
            messagebox.showinfo("Éxito", f"Creadora '{nombre}' actualizada correctamente.", parent=self); self.on_window_close()
        except sqlite3.Error as e: messagebox.showerror("Error en la Base de Datos", f"No se pudo actualizar la creadora: {e}", parent=self)

class AddEmployeeForm(ctk.CTkToplevel):
    def __init__(self, master, db_name, on_close_callback):
        super().__init__(master)
        self.db_name = db_name; self.on_close_callback = on_close_callback
        self.title("Añadir Nuevo Empleado"); self.geometry("400x500"); self.resizable(False, False)
        self.transient(master); self.grab_set(); self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Nombre:", font=("Arial", 14)).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.nombre_entry = ctk.CTkEntry(self, placeholder_text="Ej: Juan Pérez", width=200); self.nombre_entry.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Rol:", font=("Arial", 14)).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.rol_combo = ctk.CTkComboBox(self, values=["Chatter", "Manager", "Admin", "Virtual Assistant"]); self.rol_combo.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Sueldo ($):", font=("Arial", 14)).grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.sueldo_entry = ctk.CTkEntry(self, placeholder_text="Ej: 1000.00"); self.sueldo_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Ventas ($):", font=("Arial", 14)).grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.ventas_entry = ctk.CTkEntry(self, placeholder_text="Ej: 1500.00"); self.ventas_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Comisión (%):", font=("Arial", 14)).grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.comision_entry = ctk.CTkEntry(self, placeholder_text="Ej: 10"); self.comision_entry.grid(row=4, column=1, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(self, text="Notas:", font=("Arial", 14)).grid(row=5, column=0, padx=20, pady=10, sticky="nw")
        self.notas_textbox = ctk.CTkTextbox(self, height=80); self.notas_textbox.grid(row=5, column=1, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self, text="Socio Asignado:", font=("Arial", 14)).grid(row=6, column=0, padx=20, pady=10, sticky="w")
        self.partner_combo = ctk.CTkComboBox(self, values=[])
        self.partner_combo.grid(row=6, column=1, padx=20, pady=10, sticky="ew")
        self.partners_map = self.load_partners()
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Guardar Empleado", command=self.save_employee).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancelar", command=self.on_window_close, fg_color="#555555").pack(side="left", padx=10)
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def load_partners(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre FROM socios ORDER BY nombre ASC")
                partners = cursor.fetchall()
            partners_map = {name: id for id, name in partners}
            partner_names = list(partners_map.keys())
            partner_names.insert(0, "Ninguno")
            partners_map["Ninguno"] = None
            self.partner_combo.configure(values=partner_names)
            self.partner_combo.set("Ninguno")
            return partners_map
        except sqlite3.Error as e:
            messagebox.showerror("Error en DB", f"No se pudieron cargar los socios: {e}", parent=self)
            return {"Ninguno": None}

    def on_window_close(self): self.on_close_callback(); self.destroy()

    def save_employee(self):
        nombre = self.nombre_entry.get().strip(); rol = self.rol_combo.get()
        sueldo_str = self.sueldo_entry.get().strip(); ventas_str = self.ventas_entry.get().strip()
        comision_str = self.comision_entry.get().strip(); notas = self.notas_textbox.get("1.0", "end-1c").strip()
        selected_partner_name = self.partner_combo.get()
        partner_id = self.partners_map.get(selected_partner_name)

        if not nombre: messagebox.showerror("Error de Validación", "El campo 'Nombre' no puede estar vacío.", parent=self); return
        try:
            sueldo = float(sueldo_str) if sueldo_str else 0.0; ventas = float(ventas_str) if ventas_str else 0.0
            comision = float(comision_str) if comision_str else 0.0
        except ValueError: messagebox.showerror("Error de Validación", "Campos numéricos deben ser números.", parent=self); return
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO empleados (nombre, rol, sueldo, ventas, comision, notas, socio_id) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                               (nombre, rol, sueldo, ventas, comision, notas, partner_id))
            messagebox.showinfo("Éxito", f"Empleado '{nombre}' guardado.", parent=self)
            self.on_window_close()
        except sqlite3.Error as e: messagebox.showerror("Error en DB", f"No se pudo guardar: {e}", parent=self)

class EditEmployeeForm(AddEmployeeForm):
    def __init__(self, master, db_name, on_close_callback, employee_data):
        super().__init__(master, db_name, on_close_callback)
        self.title("Editar Empleado"); self.employee_id = employee_data['id']
        self.nombre_entry.insert(0, employee_data['nombre']); self.rol_combo.set(employee_data['rol'])
        self.sueldo_entry.insert(0, str(employee_data['sueldo'])); self.ventas_entry.insert(0, str(employee_data['ventas']))
        self.comision_entry.insert(0, str(employee_data['comision'])); self.notas_textbox.insert("1.0", employee_data['notas'])

        if employee_data.get('socio_id') is not None:
            partner_name = [name for name, id in self.partners_map.items() if id == employee_data.get('socio_id')]
            if partner_name:
                self.partner_combo.set(partner_name[0])

    def save_employee(self):
        nombre = self.nombre_entry.get().strip(); rol = self.rol_combo.get()
        sueldo_str = self.sueldo_entry.get().strip(); ventas_str = self.ventas_entry.get().strip()
        comision_str = self.comision_entry.get().strip(); notas = self.notas_textbox.get("1.0", "end-1c").strip()
        selected_partner_name = self.partner_combo.get()
        partner_id = self.partners_map.get(selected_partner_name)

        if not nombre: messagebox.showerror("Error de Validación", "El campo 'Nombre' no puede estar vacío.", parent=self); return
        try:
            sueldo = float(sueldo_str) if sueldo_str else 0.0; ventas = float(ventas_str) if ventas_str else 0.0
            comision = float(comision_str) if comision_str else 0.0
        except ValueError: messagebox.showerror("Error de Validación", "Campos numéricos deben ser números.", parent=self); return
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE empleados SET nombre=?, rol=?, sueldo=?, ventas=?, comision=?, notas=?, socio_id=? WHERE id=?', 
                               (nombre, rol, sueldo, ventas, comision, notas, partner_id, self.employee_id))
            messagebox.showinfo("Éxito", f"Empleado '{nombre}' actualizado.", parent=self)
            self.on_window_close()
        except sqlite3.Error as e: messagebox.showerror("Error en DB", f"No se pudo actualizar: {e}", parent=self)

# --- NUEVOS FORMULARIOS PARA SOCIOS ---
class AddPartnerForm(ctk.CTkToplevel):
    def __init__(self, master, db_name, on_close_callback):
        super().__init__(master)
        self.db_name = db_name; self.on_close_callback = on_close_callback
        self.title("Añadir Nuevo Socio"); self.geometry("400x300"); self.resizable(False, False)
        self.transient(master); self.grab_set(); self.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text="Nombre:", font=("Arial", 14)).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.nombre_entry = ctk.CTkEntry(self, placeholder_text="Ej: Socio Principal", width=200)
        self.nombre_entry.grid(row=0, column=1, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self, text="Notas:", font=("Arial", 14)).grid(row=1, column=0, padx=20, pady=10, sticky="nw")
        self.notas_textbox = ctk.CTkTextbox(self, height=100)
        self.notas_textbox.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ctk.CTkButton(button_frame, text="Guardar Socio", command=self.save_partner).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancelar", command=self.on_window_close, fg_color="#555555").pack(side="left", padx=10)
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def on_window_close(self): self.on_close_callback(); self.destroy()

    def save_partner(self):
        nombre = self.nombre_entry.get().strip()
        notas = self.notas_textbox.get("1.0", "end-1c").strip()
        if not nombre:
            messagebox.showerror("Error de Validación", "El campo 'Nombre' no puede estar vacío.", parent=self); return
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute('INSERT INTO socios (nombre, notas) VALUES (?, ?)', (nombre, notas))
            messagebox.showinfo("Éxito", f"Socio '{nombre}' guardado correctamente.", parent=self); self.on_window_close()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error en la Base de Datos", f"El socio '{nombre}' ya existe.", parent=self)
        except sqlite3.Error as e:
            messagebox.showerror("Error en la Base de Datos", f"No se pudo guardar el socio: {e}", parent=self)

class EditPartnerForm(AddPartnerForm):
    def __init__(self, master, db_name, on_close_callback, partner_data):
        super().__init__(master, db_name, on_close_callback)
        self.title("Editar Socio"); self.partner_id = partner_data['id']
        self.nombre_entry.insert(0, partner_data['nombre'])
        self.notas_textbox.insert("1.0", partner_data['notas'])

    def save_partner(self):
        nombre = self.nombre_entry.get().strip()
        notas = self.notas_textbox.get("1.0", "end-1c").strip()
        if not nombre:
            messagebox.showerror("Error de Validación", "El campo 'Nombre' no puede estar vacío.", parent=self); return
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute('UPDATE socios SET nombre=?, notas=? WHERE id=?', (nombre, notas, self.partner_id))
            messagebox.showinfo("Éxito", f"Socio '{nombre}' actualizado correctamente.", parent=self); self.on_window_close()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error en la Base de Datos", f"El socio '{nombre}' ya existe.", parent=self)
        except sqlite3.Error as e:
            messagebox.showerror("Error en la Base de Datos", f"No se pudo actualizar el socio: {e}", parent=self)

class AddTransactionForm(ctk.CTkToplevel):
    def __init__(self, master, db_name, on_close_callback):
        super().__init__(master)
        self.db_name = db_name; self.on_close_callback = on_close_callback
        self.title("Añadir Transacción"); self.geometry("450x500"); self.resizable(False, False)
        self.transient(master); self.grab_set()
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent"); main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(main_frame, text="Tipo:", font=("Arial", 14)).grid(row=0, column=0, padx=(0,10), pady=10, sticky="w")
        self.tipo_combo = ctk.CTkComboBox(main_frame, values=["ingreso", "egreso"], command=self.toggle_income_fields); self.tipo_combo.grid(row=0, column=1, columnspan=2, pady=10, sticky="ew")

        self.creator_label = ctk.CTkLabel(main_frame, text="Asociar a Creadora:", font=("Arial", 14))
        self.creator_combo = ctk.CTkComboBox(main_frame, values=[])
        self.creators_map = self.load_creators()

        ctk.CTkLabel(main_frame, text="Categoría:", font=("Arial", 14)).grid(row=2, column=0, padx=(0,10), pady=10, sticky="w")
        self.categoria_combo = ctk.CTkComboBox(main_frame, values=[]); self.categoria_combo.grid(row=2, column=1, pady=10, sticky="ew")
        self.load_categories()

        self.add_cat_button = ctk.CTkButton(main_frame, text="➕", width=30, command=self.add_new_category); self.add_cat_button.grid(row=2, column=2, padx=(5,0), pady=10, sticky="w")

        ctk.CTkLabel(main_frame, text="Monto ($):", font=("Arial", 14)).grid(row=3, column=0, padx=(0,10), pady=10, sticky="w")
        self.monto_entry = ctk.CTkEntry(main_frame, placeholder_text="Ej: 100.50"); self.monto_entry.grid(row=3, column=1, columnspan=2, pady=10, sticky="ew")
        
        self.commission_checkbox = ctk.CTkCheckBox(main_frame, text="Aplicar comisión de retiro del 2%")
        
        ctk.CTkLabel(main_frame, text="Descripción:", font=("Arial", 14)).grid(row=5, column=0, padx=(0,10), pady=10, sticky="nw")
        self.descripcion_textbox = ctk.CTkTextbox(main_frame, height=80); self.descripcion_textbox.grid(row=5, column=1, columnspan=2, pady=10, sticky="ew")
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent"); button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        ctk.CTkButton(button_frame, text="Guardar Transacción", command=self.save_transaction).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancelar", command=self.on_window_close, fg_color="#555555").pack(side="left", padx=10)
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.toggle_income_fields()

    def load_creators(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre FROM creadoras ORDER BY nombre ASC")
                creators = cursor.fetchall()
            creators_map = {name: id for id, name in creators}
            creator_names = list(creators_map.keys())
            creator_names.insert(0, "Ninguna")
            creators_map["Ninguna"] = None
            self.creator_combo.configure(values=creator_names)
            self.creator_combo.set("Ninguna")
            return creators_map
        except sqlite3.Error as e:
            messagebox.showerror("Error en DB", f"No se pudieron cargar las creadoras: {e}", parent=self)
            return {"Ninguna": None}

    def toggle_income_fields(self, event=None):
        if self.tipo_combo.get() == "ingreso":
            self.creator_label.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="w")
            self.creator_combo.grid(row=1, column=1, columnspan=2, pady=10, sticky="ew")
            self.commission_checkbox.grid(row=4, column=1, columnspan=2, pady=(5,5), sticky="w")
            self.commission_checkbox.select()
        else:
            self.creator_label.grid_forget()
            self.creator_combo.grid_forget()
            self.commission_checkbox.grid_forget()

    def load_categories(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre FROM categorias_finanzas ORDER BY nombre ASC")
                categories = [row[0] for row in cursor.fetchall()]
            self.categoria_combo.configure(values=categories)
            if categories: self.categoria_combo.set(categories[0])
        except sqlite3.Error as e: messagebox.showerror("Error en DB", f"No se pudieron cargar las categorías: {e}", parent=self)

    def add_new_category(self):
        dialog = ctk.CTkInputDialog(text="Escribe el nombre de la nueva categoría:", title="Añadir Categoría")
        new_category = dialog.get_input()
        if new_category and new_category.strip():
            try:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO categorias_finanzas (nombre) VALUES (?)", (new_category.strip(),))
                self.load_categories()
                self.categoria_combo.set(new_category.strip())
            except sqlite3.IntegrityError: messagebox.showwarning("Duplicado", f"La categoría '{new_category.strip()}' ya existe.", parent=self)
            except sqlite3.Error as e: messagebox.showerror("Error en DB", f"No se pudo guardar la categoría: {e}", parent=self)

    def on_window_close(self): self.on_close_callback(); self.destroy()

    def save_transaction(self):
        tipo = self.tipo_combo.get(); categoria = self.categoria_combo.get()
        monto_str = self.monto_entry.get().strip(); descripcion = self.descripcion_textbox.get("1.0", "end-1c").strip()
        selected_creator_name = self.creator_combo.get()
        creator_id = self.creators_map.get(selected_creator_name) if tipo == 'ingreso' else None
        apply_commission = self.commission_checkbox.get() == 1 and tipo == 'ingreso'
        if not all([monto_str, descripcion, categoria]): messagebox.showerror("Error de Validación", "Todos los campos son requeridos.", parent=self); return
        try:
            monto = float(monto_str)
        except ValueError: messagebox.showerror("Error de Validación", "'Monto' debe ser un número.", parent=self); return
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO finanzas (tipo, categoria, monto, descripcion, creadora_id) VALUES (?, ?, ?, ?, ?)',
                               (tipo, categoria, monto, descripcion, creator_id))
                if apply_commission:
                    commission_amount = monto * 0.02
                    desc_egreso = f"Comisión 2% por retiro de ${monto:.2f}"
                    cursor.execute('INSERT INTO finanzas (tipo, categoria, monto, descripcion) VALUES (?, ?, ?, ?)',
                                   ('egreso', 'Comisión Retiro Cripto', commission_amount, desc_egreso))
            messagebox.showinfo("Éxito", "Transacción guardada.", parent=self)
            self.on_window_close()
        except sqlite3.Error as e: messagebox.showerror("Error en DB", f"No se pudo guardar la transacción: {e}", parent=self)

class EditTransactionForm(AddTransactionForm):
    def __init__(self, master, db_name, on_close_callback, transaction_data):
        self.transaction_data = transaction_data
        super().__init__(master, db_name, on_close_callback)
        self.title("Editar Transacción"); self.transaction_id = transaction_data['id']
        self.tipo_combo.set(transaction_data['tipo']); self.categoria_combo.set(transaction_data['categoria'])
        self.monto_entry.insert(0, str(transaction_data['monto'])); self.descripcion_textbox.insert("1.0", transaction_data['descripcion'])
        self.toggle_income_fields()
        if transaction_data['creadora_id'] is not None:
            creator_name = [name for name, id in self.creators_map.items() if id == transaction_data['creadora_id']]
            if creator_name: self.creator_combo.set(creator_name[0])
        self.monto_entry.configure(state="disabled"); self.tipo_combo.configure(state="disabled")
        self.creator_combo.configure(state="disabled"); self.commission_checkbox.grid_remove()
        ctk.CTkLabel(self, text="La edición de transacciones está limitada.\nPara cambios mayores, elimine y cree una nueva.", text_color="orange", wraplength=380).grid(row=7, column=0, columnspan=2, padx=20)

    def save_transaction(self):
        new_categoria = self.categoria_combo.get()
        new_descripcion = self.descripcion_textbox.get("1.0", "end-1c").strip()
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE finanzas SET categoria=?, descripcion=? WHERE id=?', (new_categoria, new_descripcion, self.transaction_id))
            messagebox.showinfo("Éxito", "Transacción actualizada.", parent=self)
            self.on_window_close()
        except sqlite3.Error as e: messagebox.showerror("Error en DB", f"No se pudo actualizar la transacción: {e}", parent=self)