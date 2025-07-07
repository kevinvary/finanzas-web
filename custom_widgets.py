import customtkinter as ctk
from PIL import Image

class CollapsibleMenu(ctk.CTkFrame):
    def __init__(self, master, title, icon_path, sub_items):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.sub_items = sub_items
        self.is_open = False

        try:
            icon_image = ctk.CTkImage(Image.open(icon_path), size=(20, 20))
        except:
            icon_image = None

        self.header_button = ctk.CTkButton(
            self,
            text=f"  {title}",
            image=icon_image,
            anchor="w",
            fg_color="transparent",
            font=("Arial", 16, "bold"),
            command=self.toggle
        )
        self.header_button.pack(fill="x", padx=10, pady=5)

        self.sub_menu_frame = ctk.CTkFrame(self, fg_color="transparent")

        for item_text, item_icon_path, item_command in self.sub_items:
            try:
                sub_icon_image = ctk.CTkImage(Image.open(item_icon_path), size=(18, 18))
            except:
                sub_icon_image = None

            button = ctk.CTkButton(
                self.sub_menu_frame,
                text=f"  {item_text}",
                image=sub_icon_image,
                anchor="w",
                fg_color="transparent",
                hover_color="#333333",
                font=("Arial", 14),
                command=item_command
            )
            button.pack(fill="x", padx=25, pady=4)

    def toggle(self):
        if self.is_open:
            self.sub_menu_frame.pack_forget()
            self.is_open = False
        else:
            self.sub_menu_frame.pack(fill="x", after=self.header_button)
            self.is_open = True

class CollapsibleFrame(ctk.CTkFrame):
    """
    Un frame colapsable que contiene un header para hacer clic
    y un frame de contenido que se muestra/oculta.
    """
    def __init__(self, master, title, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.is_open = False
        
        # --- Cabecera ---
        self.header = ctk.CTkFrame(self, fg_color="#333333", corner_radius=6, height=30)
        self.header.pack(fill="x", padx=0, pady=2)
        
        self.title_label = ctk.CTkLabel(self.header, text=f"  {title}", font=("Arial", 16, "bold"), anchor="w")
        self.title_label.pack(side="left", fill="x", expand=True, padx=10)
        
        self.arrow_label = ctk.CTkLabel(self.header, text="▼", font=("Arial", 16))
        self.arrow_label.pack(side="right", padx=10)
        
        # --- Frame de Contenido (inicialmente oculto) ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # --- Binds ---
        self.header.bind("<Button-1>", self.toggle)
        self.title_label.bind("<Button-1>", self.toggle)
        self.arrow_label.bind("<Button-1>", self.toggle)

    def toggle(self, event=None):
        if self.is_open:
            self.content_frame.pack_forget()
            self.arrow_label.configure(text="▼")
            self.is_open = False
        else:
            self.content_frame.pack(fill="both", expand=True, pady=(5,0))
            self.arrow_label.configure(text="▲")
            self.is_open = True