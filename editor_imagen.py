import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser
from PIL import Image, ImageTk, ImageDraw

class ImageEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent, image_path, callback_on_save):
        super().__init__(parent)
        self.title("Editor Manual - Borrar Fondo y Anotar")
        self.geometry("1000x700")
        
        self.image_path = image_path
        self.callback_on_save = callback_on_save
        
        # Cargar imagen original (PIL)
        self.original_image = Image.open(image_path).convert("RGB")
        self.edited_image = self.original_image.copy()
        self.draw = ImageDraw.Draw(self.edited_image)
        
        # Estado de la herramienta
        # Por defecto arranca en "Negro" que servirá como goma de borrar para el fondo oscuro
        self.current_color = "black" 
        self.brush_size = 40
        self.last_x = None
        self.last_y = None
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.setup_ui()
        self.update_canvas_image()

    def setup_ui(self):
        # Panel lateral (Toolbar)
        toolbar = ctk.CTkFrame(self, width=220)
        toolbar.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        toolbar.grid_propagate(False)
        
        ctk.CTkLabel(toolbar, text="🖌️ HERRAMIENTAS", font=("Arial", 16, "bold")).pack(pady=20)
        
        ctk.CTkLabel(toolbar, text="1. Usa esto para ocultar el\nfondo gris del escáner:", text_color="gray").pack(pady=(10,0))
        ctk.CTkButton(toolbar, text="⬛ Borrador de Fondo", 
                     fg_color="#1f2937", hover_color="#000000",
                     command=lambda: self.set_color("black")).pack(pady=10, fill="x", padx=15)
                     
        ctk.CTkLabel(toolbar, text="2. Usa esto para marcar\nzonas de interés:", text_color="gray").pack(pady=(20,0))
        ctk.CTkButton(toolbar, text="🖍️ Pincel de Color", 
                     fg_color="#3b82f6", hover_color="#2563eb",
                     command=self.choose_color).pack(pady=10, fill="x", padx=15)
                     
        ctk.CTkLabel(toolbar, text="Tamaño del Pincel:").pack(pady=(30, 0))
        self.slider_size = ctk.CTkSlider(toolbar, from_=5, to=150, command=self.change_brush_size)
        self.slider_size.set(self.brush_size)
        self.slider_size.pack(pady=10, padx=15)
        
        # Botón para guardar y recalcular el mapa
        ctk.CTkButton(toolbar, text="💾 GUARDAR Y REPROCESAR", 
                     fg_color="#059669", hover_color="#047857",
                     height=50,
                     command=self.save_and_close).pack(side="bottom", pady=20, fill="x", padx=15)
                     
        # Área de dibujo (Canvas)
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Usamos tk.Canvas nativo para mejor control del dibujo
        self.canvas = tk.Canvas(canvas_frame, bg="#e5e7eb", cursor="circle")
        self.canvas.pack(fill="both", expand=True)
        
        # Eventos del mouse
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_line)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        
    def set_color(self, color):
        self.current_color = color
        
    def choose_color(self):
        color = colorchooser.askcolor(title="Elegir Color para Pincel")[1]
        if color:
            self.current_color = color
            
    def change_brush_size(self, value):
        self.brush_size = int(value)
        
    def update_canvas_image(self):
        # Para que encaje en la pantalla sin distorsionar la original al guardar
        self.tk_image = ImageTk.PhotoImage(self.edited_image)
        self.canvas.config(scrollregion=(0, 0, self.edited_image.width, self.edited_image.height))
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        
    def start_draw(self, event):
        # Convertir coordenadas del click a coordenadas reales de la imagen
        self.last_x = self.canvas.canvasx(event.x)
        self.last_y = self.canvas.canvasy(event.y)
        
    def draw_line(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.last_x and self.last_y:
            # Dibujamos en la imagen de PIL (la que se va a guardar)
            self.draw.line([self.last_x, self.last_y, x, y], 
                           fill=self.current_color, 
                           width=self.brush_size, 
                           joint="curve")
            # Actualizamos el canvas visual
            self.tk_image = ImageTk.PhotoImage(self.edited_image)
            self.canvas.itemconfig(self.canvas_image_id, image=self.tk_image)
            
        self.last_x = x
        self.last_y = y
        
    def stop_draw(self, event):
        self.last_x = None
        self.last_y = None
        
    def save_and_close(self):
        # Guardar sobre la imagen temporal original
        self.edited_image.save(self.image_path)
        
        # Avisar al main que ya guardamos para que genere el mapa de calor nuevo
        if self.callback_on_save:
            self.callback_on_save()
            
        self.destroy()