import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageTk, ImageDraw
import tkinter as tk
from tkinter import colorchooser
from config_mejorado import Config

class ImageEditorPopup(tk.Toplevel):
    """Ventana emergente avanzada para limpiar fondo, con zoom, multiselección libre y deshacer."""
    def __init__(self, parent_img_path):
        super().__init__()
        self.title("Editor de Escaneo - Aislar Pie y Limpiar Fondo")
        self.geometry("1100x800")
        
        self.image_path = parent_img_path
        self.original_image = Image.open(self.image_path).convert("RGB")
        self.edited_image = self.original_image.copy()
        self.draw = ImageDraw.Draw(self.edited_image)
        
        # Guardado automático en caso de que el usuario cierre con la X de la ventana
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)
        
        # Historial para Deshacer (Undo)
        self.undo_stack = []
        
        # Dimensiones visuales máximas (para que encaje en monitores normales)
        self.max_disp_w = 800
        self.max_disp_h = 750
        
        # Cálculo de escala para achicar la previsualización
        ratio_w = self.max_disp_w / self.edited_image.width
        ratio_h = self.max_disp_h / self.edited_image.height
        self.scale_factor = min(ratio_w, ratio_h)
        if self.scale_factor > 1: 
            self.scale_factor = 1.0 
            
        self.disp_w = int(self.edited_image.width * self.scale_factor)
        self.disp_h = int(self.edited_image.height * self.scale_factor)
        
        self.mode = "brush" # 'brush', 'select_rect', 'select_lasso'
        self.current_color = "black"  
        self.brush_size = 40
        
        # Variables de rastreo del mouse
        self.last_x, self.last_y = None, None
        self.last_cx, self.last_cy = None, None
        
        self.rect_start, self.rect_end = None, None
        self.rect_id = None
        
        # Soporte para MÚLTIPLES lazos
        self.current_lasso_disp = []
        self.current_lasso_real = []
        self.all_lassos_disp = []
        self.all_lassos_real = []
        
        self.setup_ui()
        self.update_canvas_image()
        
        # Atajos de teclado
        self.bind("<Delete>", self.delete_selection)
        self.bind("<BackSpace>", self.delete_selection)
        self.bind("<Control-z>", lambda e: self.undo())
        
        # Hace que la ventana sea modal
        self.grab_set()
        self.wait_window()

    def get_real_coords(self, cx, cy):
        return int(cx / self.scale_factor), int(cy / self.scale_factor)
        
    def save_state(self):
        """Guarda el estado actual de la imagen para poder deshacer"""
        self.undo_stack.append(self.edited_image.copy())
        if len(self.undo_stack) > 15: # Guardamos hasta 15 pasos
            self.undo_stack.pop(0)
            
    def undo(self):
        """Vuelve al paso anterior"""
        if self.undo_stack:
            self.edited_image = self.undo_stack.pop()
            self.draw = ImageDraw.Draw(self.edited_image)
            self.update_canvas_image()
            self.clear_selection_visuals()

    def setup_ui(self):
        toolbar = tk.Frame(self, width=250, bg="#1f2937")
        toolbar.pack(side="left", fill="y")
        toolbar.pack_propagate(False) 
        
        tk.Label(toolbar, text="🖌️ HERRAMIENTAS", fg="white", bg="#1f2937", font=("Arial", 14, "bold")).pack(pady=(20, 10))
        
        tk.Button(toolbar, text="↩️ Deshacer (Ctrl+Z)", bg="#4b5563", fg="white", font=("Arial", 9, "bold"), command=self.undo).pack(fill="x", padx=15, pady=(0,10))
        
        # MODO PINCEL
        tk.Label(toolbar, text="--- DIBUJO ---", fg="#9ca3af", bg="#1f2937").pack(pady=(5,5))
        btn_brush = tk.Button(toolbar, text="🖊️ Pincel Libre", bg="#3b82f6", fg="white", font=("Arial", 10, "bold"), command=lambda: self.set_mode("brush"))
        btn_brush.pack(fill="x", padx=15, pady=2)
        tk.Button(toolbar, text="⬛ Pincel Negro (Borrar)", bg="black", fg="white", command=lambda: self.set_color("black")).pack(fill="x", padx=15, pady=2)
                     
        tk.Label(toolbar, text="Tamaño Pincel:", fg="white", bg="#1f2937").pack(pady=(10, 0))
        self.slider_size = tk.Scale(toolbar, from_=5, to=300, orient="horizontal", bg="#1f2937", fg="white", highlightthickness=0, command=self.change_brush_size)
        self.slider_size.set(self.brush_size)
        self.slider_size.pack(pady=5, padx=15)
        
        # MODO SELECCIÓN
        tk.Label(toolbar, text="--- SELECCIÓN ---", fg="#9ca3af", bg="#1f2937").pack(pady=(15,5))
        btn_select = tk.Button(toolbar, text="🔲 Cuadro", bg="#8b5cf6", fg="white", font=("Arial", 10, "bold"), command=lambda: self.set_mode("select_rect"))
        btn_select.pack(fill="x", padx=15, pady=2)
        
        btn_lasso = tk.Button(toolbar, text="✍️ Lazo (Multiselección)", bg="#ec4899", fg="white", font=("Arial", 10, "bold"), command=lambda: self.set_mode("select_lasso"))
        btn_lasso.pack(fill="x", padx=15, pady=2)
        
        tk.Label(toolbar, text="Acciones de Selección:", fg="#d1d5db", bg="#1f2937", font=("Arial", 9)).pack(pady=(10,0))
        btn_crop = tk.Button(toolbar, text="✂️ Aislar (Dejar SOLO esto)", bg="#10b981", fg="white", command=self.crop_to_selection)
        btn_crop.pack(fill="x", padx=15, pady=2)
        btn_del = tk.Button(toolbar, text="🗑️ Borrar interior (Supr)", bg="#ef4444", fg="white", command=lambda: self.delete_selection(None))
        btn_del.pack(fill="x", padx=15, pady=2)
        
        # GUARDAR
        tk.Button(toolbar, text="💾 GUARDAR\nY CONTINUAR", bg="#059669", fg="white", font=("Arial", 12, "bold"), height=3, command=self.save_and_close).pack(side="bottom", pady=20, fill="x", padx=15)
                     
        canvas_frame = tk.Frame(self, bg="#111827")
        canvas_frame.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#e5e7eb", cursor="none", highlightthickness=0)
        self.canvas.pack(padx=20, pady=20)
        
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_line)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.canvas.bind("<Motion>", self.on_mouse_move) # Para mostrar el cursor del pincel
        
    def clear_selection_visuals(self):
        if self.rect_id: self.canvas.delete(self.rect_id)
        self.canvas.delete("lasso_line")
        self.rect_start, self.rect_end = None, None
        self.current_lasso_disp = []
        self.current_lasso_real = []
        self.all_lassos_disp = []
        self.all_lassos_real = []
        
    def set_mode(self, mode):
        self.mode = mode
        self.clear_selection_visuals()
        if mode == "brush":
            self.canvas.config(cursor="none") 
        else:
            self.canvas.config(cursor="cross")
            self.canvas.delete("brush_cursor")
            
    def set_color(self, color):
        self.current_color = color
        self.set_mode("brush")
        
    def change_brush_size(self, value):
        self.brush_size = int(value)
        
    def update_canvas_image(self):
        display_img = self.edited_image.resize((self.disp_w, self.disp_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(display_img)
        self.canvas.config(width=self.disp_w, height=self.disp_h)
        self.canvas.delete("base_img")
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image, tags="base_img")
        self.canvas.tag_lower("base_img")
        
    def update_brush_cursor(self, cx, cy):
        self.canvas.delete("brush_cursor")
        if self.mode == "brush":
            r = (self.brush_size * self.scale_factor) / 2.0
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="white", tags="brush_cursor")
            self.canvas.create_oval(cx-r-1, cy-r-1, cx+r+1, cy+r+1, outline="black", tags="brush_cursor")

    def on_mouse_move(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.update_brush_cursor(cx, cy)
        
    def start_draw(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        rx, ry = self.get_real_coords(cx, cy)
        
        if self.mode == "brush":
            self.save_state()
            self.last_x, self.last_y = rx, ry
            self.last_cx, self.last_cy = cx, cy
            
            r_real = self.brush_size / 2.0
            self.draw.ellipse([rx-r_real, ry-r_real, rx+r_real, ry+r_real], fill=self.current_color)
            
            self.update_brush_cursor(cx, cy)
            
        elif self.mode == "select_rect":
            self.clear_selection_visuals()
            self.rect_start = (cx, cy)
            self.rect_id = self.canvas.create_rectangle(cx, cy, cx, cy, outline="red", width=2, dash=(4, 4))
            
        elif self.mode == "select_lasso":
            self.current_lasso_disp = [(cx, cy)]
            self.current_lasso_real = [(rx, ry)]
            
    def draw_line(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        rx, ry = self.get_real_coords(cx, cy)
        
        if self.mode == "brush" and self.last_x is not None:
            self.draw.line([self.last_x, self.last_y, rx, ry], fill=self.current_color, width=self.brush_size, joint="curve")
            r_real = self.brush_size / 2.0
            self.draw.ellipse([rx-r_real, ry-r_real, rx+r_real, ry+r_real], fill=self.current_color)
            
            disp_width = max(1, self.brush_size * self.scale_factor)
            self.canvas.create_line(self.last_cx, self.last_cy, cx, cy, fill=self.current_color, width=disp_width, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags="temp_draw")
            
            self.last_x, self.last_y = rx, ry
            self.last_cx, self.last_cy = cx, cy
            self.update_brush_cursor(cx, cy)
            
        elif self.mode == "select_rect" and self.rect_start is not None:
            self.canvas.coords(self.rect_id, self.rect_start[0], self.rect_start[1], cx, cy)
            
        elif self.mode == "select_lasso" and self.current_lasso_disp:
            self.current_lasso_disp.append((cx, cy))
            self.current_lasso_real.append((rx, ry))
            p1 = self.current_lasso_disp[-2]
            p2 = self.current_lasso_disp[-1]
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="red", width=2, tags="lasso_line")
            
    def stop_draw(self, event):
        if self.mode == "brush":
            self.last_x = None
            self.last_y = None
            self.update_canvas_image()
            self.canvas.delete("temp_draw")
        elif self.mode == "select_rect" and self.rect_start:
            self.rect_end = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            self.canvas.focus_set()
        elif self.mode == "select_lasso" and len(self.current_lasso_disp) > 2:
            p1 = self.current_lasso_disp[-1]
            p2 = self.current_lasso_disp[0]
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="red", width=2, tags="lasso_line")
            
            self.all_lassos_real.append(self.current_lasso_real)
            self.all_lassos_disp.append(self.current_lasso_disp)
            
            self.current_lasso_disp = []
            self.current_lasso_real = []
            self.canvas.focus_set()
            
    def delete_selection(self, event):
        if self.mode == "select_rect" and self.rect_start and self.rect_end:
            self.save_state()
            rsx, rsy = self.get_real_coords(self.rect_start[0], self.rect_start[1])
            rex, rey = self.get_real_coords(self.rect_end[0], self.rect_end[1])
            x0, x1 = min(rsx, rex), max(rsx, rex)
            y0, y1 = min(rsy, rey), max(rsy, rey)
            self.draw.rectangle([x0, y0, x1, y1], fill="black")
            self.update_canvas_image()
            self.clear_selection_visuals()
            
        elif self.mode == "select_lasso" and self.all_lassos_real:
            self.save_state()
            for lasso in self.all_lassos_real:
                self.draw.polygon(lasso, fill="black")
            self.update_canvas_image()
            self.clear_selection_visuals()
            
    def crop_to_selection(self):
        if self.mode == "select_rect" and self.rect_start and self.rect_end:
            self.save_state()
            rsx, rsy = self.get_real_coords(self.rect_start[0], self.rect_start[1])
            rex, rey = self.get_real_coords(self.rect_end[0], self.rect_end[1])
            x0, x1 = min(rsx, rex), max(rsx, rex)
            y0, y1 = min(rsy, rey), max(rsy, rey)
            
            new_img = Image.new("RGB", self.edited_image.size, "black")
            cropped = self.edited_image.crop((x0, y0, x1, y1))
            new_img.paste(cropped, (int(x0), int(y0)))
            
            self.edited_image = new_img
            self.draw = ImageDraw.Draw(self.edited_image)
            self.update_canvas_image()
            self.clear_selection_visuals()
            
        elif self.mode == "select_lasso" and self.all_lassos_real:
            self.save_state()
            
            mask = Image.new("L", self.edited_image.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            
            for lasso in self.all_lassos_real:
                mask_draw.polygon(lasso, fill=255)
            
            new_img = Image.new("RGB", self.edited_image.size, "black")
            new_img.paste(self.edited_image, (0, 0), mask)
            
            self.edited_image = new_img
            self.draw = ImageDraw.Draw(self.edited_image)
            self.update_canvas_image()
            self.clear_selection_visuals()

    def save_and_close(self):
        self.edited_image.save(self.image_path)
        self.destroy()

class ImageAnalyzer:

    @staticmethod
    def analizar_presion(image_path, output_path, intensidad=1.5):
        try:
            img = cv2.imread(image_path)
            if img is None: return None
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # --- LÓGICA DIGITAL: TOLERANTE PERO LIMPIA ---
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)
            
            _, thresh = cv2.threshold(blurred, 25, 255, cv2.THRESH_BINARY)
            
            # Ignorar fondo blanco puro para que no rompa el mapa
            _, mask_white = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
            thresh[mask_white == 255] = 0
            
            kernel_ruido = np.ones((11, 11), np.uint8)
            thresh_limpio = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_ruido)
            
            contours, _ = cv2.findContours(thresh_limpio, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            mask_final = np.zeros_like(gray)
            
            if contours:
                for c in contours:
                    if cv2.contourArea(c) > 1000:
                         cv2.drawContours(mask_final, [c], -1, 255, thickness=cv2.FILLED)
                         
                kernel_cierre = np.ones((35, 35), np.uint8)
                mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel_cierre)
            # -------------------------------------------

            # 3. PROCESAR MAPA DE CALOR
            proc_gray = gray.copy()
            proc_gray = cv2.multiply(proc_gray.astype(np.float32), intensidad)
            proc_gray = np.clip(proc_gray, 0, 255).astype(np.uint8)
            proc_gray = cv2.bitwise_and(proc_gray, proc_gray, mask=mask_final)
            
            proc_gray = cv2.GaussianBlur(proc_gray, (25, 25), 0)
            heatmap = cv2.applyColorMap(proc_gray, cv2.COLORMAP_JET)
            
            # 4. MEZCLA CON ORIGINAL (Overlay)
            resultado = cv2.addWeighted(heatmap, 0.4, img, 0.6, 0)
            
            # Fondo Blanco Forzado
            mask_inv = cv2.bitwise_not(mask_final)
            resultado[mask_inv > 0] = [255, 255, 255]
            
            # 5. GUARDAR Y RETORNAR STATS
            cv2.imwrite(output_path, resultado)
            return {
                'presion_media': np.mean(proc_gray[mask_final > 0]) if np.any(mask_final) else 0,
                'presion_max': np.max(proc_gray[mask_final > 0]) if np.any(mask_final) else 0,
                'area_contacto_mm2': np.sum(mask_final > 0) * 0.0625,
                'distribucion': {'anterior': 33, 'media': 33, 'posterior': 34}
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def unir_imagenes(path_izq, path_der, path_salida, alinear=True):
        """Une dos imágenes lado a lado"""
        try:
            img_i = Image.open(path_izq)
            img_d = Image.open(path_der)
            dpi_i = img_i.info.get("dpi")
            
            h = max(img_i.height, img_d.height)
            wi = int(img_i.width * (h / img_i.height))
            wd = int(img_d.width * (h / img_d.height))
            
            img_i_resized = img_i.resize((wi, h), Image.Resampling.LANCZOS)
            img_d_resized = img_d.resize((wd, h), Image.Resampling.LANCZOS)
            
            gap = 20
            unida = Image.new("RGB", (wi + wd + gap, h), (255, 255, 255))
            unida.paste(img_i_resized, (0, 0))
            unida.paste(img_d_resized, (wi + gap, 0))
            
            save_kwargs = {}
            if dpi_i and isinstance(dpi_i, tuple) and len(dpi_i) >= 2:
                save_kwargs["dpi"] = (int(dpi_i[0]), int(dpi_i[1]))
            unida.save(path_salida, **save_kwargs)
            return True
        except Exception as e:
            print(f"Error uniendo imágenes: {e}")
            return False
    
    @staticmethod
    def detectar_calibracion_automatica(img_shape, path_img=None, devolver_fuente=False):
        """Detecta automáticamente la escala (prioriza DPI real del escáner)."""
        # 1) Intentar DPI embebido en metadata del archivo
        if path_img:
            try:
                pil = Image.open(path_img)
                dpi = pil.info.get("dpi")
                if dpi and dpi[0] and dpi[0] > 0:
                    pixels_por_mm = float(dpi[0]) / 25.4
                    pixels_por_mm *= Config.CALIBRACION_CORRECCION_PXMM
                    print(f"═══ CALIBRACIÓN AUTOMÁTICA (DPI) ═══")
                    print(f"DPI detectado: {dpi[0]:.1f}")
                    print(f"Corrección: x{Config.CALIBRACION_CORRECCION_PXMM:.2f}")
                    print(f"Escala: {pixels_por_mm:.2f} px/mm")
                    return (pixels_por_mm, "DPI") if devolver_fuente else pixels_por_mm
            except Exception:
                pass

        # 2) Fallback geométrico (A4). Si parece imagen unida de 2 capturas, compensar ancho.
        altura_img, ancho_img = img_shape[:2]
        ancho_efectivo = ancho_img / 2 if (ancho_img / max(altura_img, 1)) > 1.2 else ancho_img

        escala_ancho = ancho_efectivo / 210  # A4 ancho mm
        escala_alto = altura_img / 297       # A4 alto mm
        pixels_por_mm = (escala_ancho + escala_alto) / 2
        pixels_por_mm *= Config.CALIBRACION_CORRECCION_PXMM

        print(f"═══ CALIBRACIÓN AUTOMÁTICA (A4 fallback) ═══")
        print(f"Imagen: {ancho_img} x {altura_img} px")
        print(f"Corrección: x{Config.CALIBRACION_CORRECCION_PXMM:.2f}")
        print(f"Escala: {pixels_por_mm:.2f} px/mm")
        return (pixels_por_mm, "A4") if devolver_fuente else pixels_por_mm


    @staticmethod
    def analizar_imagen(path_img, modo="Digital", colormap_name="Turbo", intensidad=1.0, suavizado=True):
        """
        VERSIÓN FINAL con Editor Integrado, Marca de Agua Inteligente y Exclusión de Blancos.
        """
        COLORMAP_IDS = {
            'Jet (Clásico)': cv2.COLORMAP_JET,
            'Arcoíris': cv2.COLORMAP_RAINBOW,
            'Caliente': cv2.COLORMAP_HOT,
            'Hot': cv2.COLORMAP_HOT,
            'Inferno': cv2.COLORMAP_INFERNO, 
            'Océano': cv2.COLORMAP_OCEAN,
            'Verano': cv2.COLORMAP_SUMMER,
            'Invierno': cv2.COLORMAP_WINTER,
            'Turbo': cv2.COLORMAP_TURBO,
            'Viridis': cv2.COLORMAP_VIRIDIS,
        }
        
        colormap_id = COLORMAP_IDS.get(colormap_name, cv2.COLORMAP_JET)
        
        print(f"\n═══ DETECCIÓN DE PIE ═══")
        print(f"Modo: {modo}")

        # Cargar imagen inicial para chequear si ya la procesamos en esta sesión
        img = cv2.imread(path_img)
        if img is None:
            raise ValueError("No se pudo cargar la imagen")
            
        # Detección de MARCA DE AGUA (Pixel 0,0 configurado por nosotros)
        ya_procesada = False
        if img.shape[0] > 0 and img.shape[1] > 0:
            p = img[0, 0]
            # OpenCV carga en BGR. Buscamos el código secreto: [252, 253, 254]
            if p[0] == 252 and p[1] == 253 and p[2] == 254:
                ya_procesada = True

        if modo == "Digital" and not ya_procesada and Config.AUTO_ABRIR_EDITOR_ESCANEO:
            print("Abriendo editor de imagen manual para limpiar el fondo...")
            ImageEditorPopup(path_img)
            print("Edición manual finalizada. Continuando proceso...")
            # Volver a cargar porque el usuario acaba de editarla y guardarla
            img = cv2.imread(path_img)
            if img is None:
                raise ValueError("No se pudo cargar la imagen tras edición")
        else:
            print("Procesamiento automático activado (sin editor manual).")
        
        # CALIBRACIÓN AUTOMÁTICA
        pixels_por_mm, fuente_calibracion = ImageAnalyzer.detectar_calibracion_automatica(
            img.shape,
            path_img=path_img,
            devolver_fuente=True,
        )
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mask_final = np.zeros_like(gray)

        # ============================================
        # PROCESAMIENTO SEGÚN MODO
        # ============================================
        if modo == "Tinta (Papel)":
            # --- CÓDIGO INTACTO ORIGINAL PARA TINTA ---
            gray_proc = gray.copy()
            _, gray_proc = cv2.threshold(gray_proc, 200, 255, cv2.THRESH_TOZERO_INV)
            gray_proc = cv2.bitwise_not(gray_proc)

            blur = cv2.GaussianBlur(gray_proc, (5, 5), 0)
            otsu_val, _ = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            print(f"Umbral Otsu: {otsu_val}")
            
            def _mask_from_contour(mask, contour):
                mask_out = np.zeros_like(mask)
                cv2.drawContours(mask_out, [contour], -1, 255, -1)
                return mask_out        
            
            def _construir_mascara(umbral_bajo, umbral_alto, open_iter=2, close_iter=2):
                _, mask_loose = cv2.threshold(gray_proc, umbral_bajo, 255, cv2.THRESH_BINARY)
                _, mask_strict = cv2.threshold(gray_proc, umbral_alto, 255, cv2.THRESH_BINARY)

                kernel = np.ones((5, 5), np.uint8)
                mask_loose = cv2.morphologyEx(mask_loose, cv2.MORPH_OPEN, kernel, iterations=open_iter)
                mask_loose = cv2.morphologyEx(mask_loose, cv2.MORPH_CLOSE, kernel, iterations=close_iter)

                mask_strict = cv2.morphologyEx(mask_strict, cv2.MORPH_OPEN, kernel, iterations=open_iter)
                mask_strict = cv2.morphologyEx(mask_strict, cv2.MORPH_CLOSE, kernel, iterations=1)

                contours_strict, _ = cv2.findContours(mask_strict, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                seed_mask = None
                if contours_strict:
                    seed_contour = max(contours_strict, key=cv2.contourArea)
                    seed_mask = _mask_from_contour(mask_strict, seed_contour)

                contours_loose, _ = cv2.findContours(mask_loose, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                mask_final = None
                if contours_loose:
                    if seed_mask is not None:
                        best_overlap = -1
                        best_contour = None
                        for contour in contours_loose:
                            candidate_mask = _mask_from_contour(mask_loose, contour)
                            overlap = cv2.countNonZero(cv2.bitwise_and(candidate_mask, seed_mask))
                            if overlap > best_overlap:
                                best_overlap = overlap
                                best_contour = contour
                        if best_contour is not None and best_overlap > 0:
                            mask_final = _mask_from_contour(mask_loose, best_contour)
                    if mask_final is None:
                        best_contour = max(contours_loose, key=cv2.contourArea)
                        mask_final = _mask_from_contour(mask_loose, best_contour)

                return mask_final if mask_final is not None else mask_loose

            umbral_bajo = max(int(otsu_val * 0.7), 20)
            umbral_alto = max(int(otsu_val * 1.1), 40)
            print(f"Umbrales usados: bajo={umbral_bajo}, alto={umbral_alto}")

            mask_final = _construir_mascara(umbral_bajo, umbral_alto)

            area_pie = np.sum(mask_final > 0)
            area_total = mask_final.shape[0] * mask_final.shape[1]
            porcentaje = (area_pie / area_total) * 100 if area_total else 0

            if porcentaje > 60:
                umbral_bajo = max(int(otsu_val * 0.9), 30)
                umbral_alto = max(int(otsu_val * 1.3), 60)
                print(f"Ajuste por fondo incluido: bajo={umbral_bajo}, alto={umbral_alto}")
                mask_final = _construir_mascara(umbral_bajo, umbral_alto, open_iter=3, close_iter=1)
            elif porcentaje < 2:
                umbral_bajo = max(int(otsu_val * 0.5), 10)
                umbral_alto = max(int(otsu_val * 0.9), 30)
                print(f"Ajuste por talón excluido: bajo={umbral_bajo}, alto={umbral_alto}")
                mask_final = _construir_mascara(umbral_bajo, umbral_alto, open_iter=1, close_iter=3)

            if np.any(mask_final):
                mean_in = float(np.mean(gray_proc[mask_final > 0]))
                mean_out = float(np.mean(gray_proc[mask_final == 0]))
                if mean_in < mean_out:
                    print("Máscara invertida detectada, invirtiendo selección.")
                    mask_final = cv2.bitwise_not(mask_final)
                    
            kernel_cierre = np.ones((25, 25), np.uint8)
            mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel_cierre, iterations=1)

        else:
            # --- NUEVA LÓGICA PARA DIGITAL: TRAS LIMPIEZA MANUAL ---
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)

            _, thresh = cv2.threshold(blurred, 25, 255, cv2.THRESH_BINARY)
            
            # SOLUCIÓN: Excluir el fondo blanco puro que nosotros mismos generamos
            _, mask_white = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
            thresh[mask_white == 255] = 0
            
            kernel_ruido = np.ones((11, 11), np.uint8)
            thresh_limpio = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_ruido)

            contours, _ = cv2.findContours(thresh_limpio, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            mask_final = np.zeros_like(gray)
            if contours:
                for c in contours:
                    if cv2.contourArea(c) > 1000:
                         cv2.drawContours(mask_final, [c], -1, 255, thickness=cv2.FILLED)
                         
                kernel_cierre = np.ones((35, 35), np.uint8)
                mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel_cierre)
                
                mask_final = cv2.GaussianBlur(mask_final, (5, 5), 0)
                _, mask_final = cv2.threshold(mask_final, 127, 255, cv2.THRESH_BINARY)

            gray_proc = gray.copy() 

        mask_inv = cv2.bitwise_not(mask_final)
        
        area_pie = np.sum(mask_final > 0)
        area_total = mask_final.shape[0] * mask_final.shape[1]
        porcentaje = (area_pie / area_total) * 100
        
        print(f"Área pie: {porcentaje:.1f}% de la imagen")
        
        # ============================================
        # FONDO BLANCO FORZADO Y NORMALIZACIÓN
        # ============================================
        gray_limpio = np.full_like(gray, 255, dtype=np.uint8)
        
        if modo == "Tinta (Papel)":
            # CORRECCIÓN PARA TINTA: Invertimos los valores para que el negro(0) sea máxima presión(255)
            gray_invertido = cv2.bitwise_not(gray)
            gray_limpio[mask_final > 0] = gray_invertido[mask_final > 0]
        else:
            gray_limpio[mask_final > 0] = gray[mask_final > 0]
        
        if suavizado:
            pie_suavizado = cv2.GaussianBlur(gray_limpio, (5, 5), 0)
            gray_limpio[mask_final > 0] = pie_suavizado[mask_final > 0]
        
        pie_pixels = gray_limpio[mask_final > 0]
        
        if len(pie_pixels) > 0:
            min_val = np.min(pie_pixels)
            max_val = np.max(pie_pixels)
            
            if max_val > min_val:
                gray_normalizado = np.full_like(gray_limpio, 255, dtype=np.uint8)
                pie_norm = ((pie_pixels - min_val) / (max_val - min_val) * 255)
                pie_norm = np.clip(pie_norm, 0, 255).astype(np.uint8)
                gray_normalizado[mask_final > 0] = pie_norm
            else:
                gray_normalizado = gray_limpio
        else:
            gray_normalizado = gray_limpio
        
        # ============================================
        # IMAGEN ORIGINAL con FONDO BLANCO Y MARCA SECRETA
        # ============================================
        orig_white = np.full_like(img, 255)
        orig_white[mask_final > 0] = img[mask_final > 0]
        orig_white[mask_final == 0] = [255, 255, 255] # Fondo blanco puro garantizado
        
        # MARCA DE AGUA INVISIBLE en el primer píxel superior izquierdo
        if modo == "Digital":
            orig_white[0, 0] = [252, 253, 254]
        
        # ============================================
        # MAPA DE CALOR con FONDO BLANCO
        # ============================================
        gray_for_heatmap = gray_normalizado.copy()

        # Homogeneizar gradientes dentro de la huella (separado por modo)
        if modo == "Tinta (Papel)":
            k_median = int(Config.HEATMAP_HOMOGENEIDAD_TINTA_MEDIAN)
            k_gauss = int(Config.HEATMAP_HOMOGENEIDAD_TINTA_GAUSS)
        else:
            k_median = int(Config.HEATMAP_HOMOGENEIDAD_DIGITAL_MEDIAN)
            k_gauss = int(Config.HEATMAP_HOMOGENEIDAD_DIGITAL_GAUSS)

        # Asegurar kernels impares para OpenCV
        if k_median % 2 == 0:
            k_median += 1
        if k_gauss % 2 == 0:
            k_gauss += 1

        if k_median > 1:
            gray_suave = cv2.medianBlur(gray_for_heatmap, k_median)
            gray_for_heatmap[mask_final > 0] = gray_suave[mask_final > 0]

        if k_gauss > 1:
            gray_suave = cv2.GaussianBlur(gray_for_heatmap, (k_gauss, k_gauss), 0)
            gray_for_heatmap[mask_final > 0] = gray_suave[mask_final > 0]

        if intensidad != 1.0 and len(pie_pixels) > 0:
            valores = gray_for_heatmap[mask_final > 0].astype(np.float32)
            valores = valores * intensidad
            valores = np.clip(valores, 0, 255).astype(np.uint8)
            gray_for_heatmap[mask_final > 0] = valores
        
        heatmap = cv2.applyColorMap(gray_for_heatmap, colormap_id)
        
        # BLANQUEADO DEFINITIVO DEL MAPA: ignoramos la intensidad si es fondo
        heatmap[mask_final == 0] = [255, 255, 255]
        
        # SOLUCIÓN EXCLUSIVA TINTA: El papel en blanco (valores altos en el escaneo original)
        # no debe pintarse de azul oscuro, lo forzamos a blanco puro.
        if modo == "Tinta (Papel)":
            papel = gray > 200
            heatmap[papel] = [255, 255, 255]
        
        # ============================================
        # ESTADÍSTICAS
        # ============================================
        valores_presion = gray_normalizado[mask_final > 0]
        area_mm2 = area_pie / (pixels_por_mm ** 2)
        
        stats = {
            'presion_media': float(np.mean(valores_presion)) if len(valores_presion) > 0 else 0,
            'presion_max': float(np.max(valores_presion)) if len(valores_presion) > 0 else 0,
            'presion_min': float(np.min(valores_presion)) if len(valores_presion) > 0 else 0,
            'area_contacto_px': int(area_pie),
            'area_contacto_mm2': area_mm2,
            'pixels_por_mm': pixels_por_mm,
            'fuente_calibracion': fuente_calibracion,
            'distribucion': ImageAnalyzer._calcular_distribucion(gray_normalizado, mask_final)
        }
        
        print(f"Área: {area_mm2/100:.1f} cm²")
        print(f"════════════════════\n")
        
        img_orig_pil = Image.fromarray(cv2.cvtColor(orig_white, cv2.COLOR_BGR2RGB))
        img_heatmap_pil = Image.fromarray(cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB))
        
        return img_orig_pil, img_heatmap_pil, stats

    @staticmethod
    def _calcular_distribucion(gray_proc, mask):
        """Calcula distribución por zonas"""
        h, w = gray_proc.shape
        
        zona_anterior = gray_proc[:h//3, :][mask[:h//3, :] > 0]
        zona_media = gray_proc[h//3:2*h//3, :][mask[h//3:2*h//3, :] > 0]
        zona_posterior = gray_proc[2*h//3:, :][mask[2*h//3:, :] > 0]
        
        return {
            'anterior': float(np.mean(zona_anterior)) if len(zona_anterior) > 0 else 0,
            'media': float(np.mean(zona_media)) if len(zona_media) > 0 else 0,
            'posterior': float(np.mean(zona_posterior)) if len(zona_posterior) > 0 else 0,
        }

    @staticmethod
    def mejorar_contraste(img_pil, factor=1.5):
        """Mejora el contraste"""
        enhancer = ImageEnhance.Contrast(img_pil)
        return enhancer.enhance(factor)

    @staticmethod
    def aplicar_filtro_sharpen(img_pil):
        """Aplica filtro de enfoque"""
        return img_pil.filter(ImageFilter.SHARPEN)

    @staticmethod
    def detectar_contornos(path_img):
        """Detecta contornos"""
        img = cv2.imread(path_img, cv2.IMREAD_GRAYSCALE)
        _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > 1000]
        return contours

    @staticmethod
    def calcular_centro_presion(gray_proc, mask):
        """Calcula centro de presión"""
        y_coords, x_coords = np.indices(gray_proc.shape)
        valores = gray_proc[mask > 0]
        x_vals = x_coords[mask > 0]
        y_vals = y_coords[mask > 0]
        
        if len(valores) == 0:
            return None, None
        
        x_cop = np.average(x_vals, weights=valores)
        y_cop = np.average(y_vals, weights=valores)
        
        return int(x_cop), int(y_cop)

    @staticmethod
    def generar_comparacion(img1_path, img2_path, output_path):
        """Genera comparación lado a lado"""
        try:
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            
            max_h = max(img1.height, img2.height)
            img1 = img1.resize((int(img1.width * max_h / img1.height), max_h), Image.Resampling.LANCZOS)
            img2 = img2.resize((int(img2.width * max_h / img2.height), max_h), Image.Resampling.LANCZOS)
            
            total_w = img1.width + img2.width + 20
            comparacion = Image.new('RGB', (total_w, max_h), 'white')
            comparacion.paste(img1, (0, 0))
            comparacion.paste(img2, (img1.width + 20, 0))
            
            comparacion.save(output_path)
            return True
        except Exception as e:
            print(f"Error generando comparación: {e}")
            return False
