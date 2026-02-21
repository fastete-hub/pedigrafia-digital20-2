from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
import os, json
from datetime import datetime

class PDFManager:
    @staticmethod
    def _wrap_text(c, text, x, y, width):
        """Envuelve texto largo en múltiples líneas, respetando los saltos de línea (Enter) del usuario"""
        # Separar primero por los "Enter" reales que haya hecho el usuario o el sistema
        lineas_manuales = text.split('\n')
        
        for linea in lineas_manuales:
            words = linea.split(' ')
            
            # Si es un renglón vacío (el usuario tocó Enter dos veces)
            if not words or all(w == '' for w in words):
                y -= 14
                continue
                
            line = []
            for word in words:
                if not word: continue
                line.append(word)
                # Si la línea actual es más ancha que el margen, bajamos
                if c.stringWidth(' '.join(line)) > width:
                    line.pop()
                    c.drawString(x, y, ' '.join(line))
                    line = [word]
                    y -= 14
            
            # Dibujar la línea restante
            if line:
                c.drawString(x, y, ' '.join(line))
                y -= 14 # Bajar el cursor para el próximo renglón
                
        return y

    @staticmethod
    def generar_simple(paciente, informe, ruta):
        """
        Genera un PDF profesional con AMBAS imágenes:
        - Imagen original (procesada con fondo blanco)
        - Mapa de calor
        """
        c = canvas.Canvas(ruta, pagesize=A4)
        w, h = A4
        
        # ===================================
        # HEADER CON ESTILO
        # ===================================
        c.setFillColor(HexColor("#0f172a"))
        c.rect(0, h-80, w, 80, fill=True, stroke=False)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(w/2, h-45, "REPORTE DE PRESIONES DE PISADA")
        
        # ===================================
        # INFORMACIÓN DEL PACIENTE
        # ===================================
        c.setFillColor(HexColor("#000000"))
        y = h - 110
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, f"Paciente: {paciente[1]}")
        c.drawString(400, y, f"Fecha: {informe[1]}")
        
        y -= 18
        c.setFont("Helvetica", 10)
        datos_paciente = f"Edad: {paciente[2]} años"
        if paciente[3]:  # Obra social
            datos_paciente += f" | OS: {paciente[3]}"
        if paciente[6]:  # Talle
            datos_paciente += f" | Talle pie: {paciente[6]} mm"
        c.drawString(50, y, datos_paciente)
        
        # ===================================
        # SECCIÓN DE IMÁGENES (MEJORADA)
        # ===================================
        y -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "ANÁLISIS VISUAL:")
        c.setStrokeColor(HexColor("#0f172a"))
        c.line(50, y-3, 550, y-3)
        
        y -= 250
        
        # Buscar las imágenes con los nombres correctos
        imagen_original = informe[3]  # Path guardado en la BD
        
        # Construir path del mapa de calor
        if "_original.png" in imagen_original:
            imagen_mapa = imagen_original.replace("_original.png", "_mapa_calor.png")
        else:
            # Fallback: buscar en el mismo directorio
            dir_estudio = os.path.dirname(imagen_original)
            if os.path.exists(dir_estudio):
                archivos = os.listdir(dir_estudio)
                mapa_files = [f for f in archivos if "mapa" in f.lower() and f.endswith(".png")]
                imagen_mapa = os.path.join(dir_estudio, mapa_files[0]) if mapa_files else None
            else:
                imagen_mapa = None
        
        # Mostrar ambas imágenes
        imagenes_mostradas = 0
        
        if os.path.exists(imagen_original):
            # Imagen Original (Izquierda)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(HexColor("#374151"))
            c.drawCentredString(w/4 + 20, y+220, "ESCANEO ORIGINAL")
            
            # Borde decorativo
            c.setStrokeColor(HexColor("#e5e7eb"))
            c.setLineWidth(2)
            c.rect(45, y-5, 250, 210, fill=False, stroke=True)
            
            try:
                c.drawImage(imagen_original, 50, y, width=240, height=200, preserveAspectRatio=True, mask='auto')
                imagenes_mostradas += 1
            except Exception:
                c.setFont("Helvetica", 8)
                c.setFillColor(HexColor("#ef4444"))
                c.drawString(60, y+100, "Error cargando imagen")
        
        if imagen_mapa and os.path.exists(imagen_mapa):
            # Mapa de Calor (Derecha)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(HexColor("#374151"))
            c.drawCentredString(3*w/4 - 20, y+220, "MAPA DE PRESIONES")
            
            # Borde decorativo
            c.setStrokeColor(HexColor("#e5e7eb"))
            c.setLineWidth(2)
            c.rect(300, y-5, 250, 210, fill=False, stroke=True)
            
            try:
                c.drawImage(imagen_mapa, 305, y, width=240, height=200, preserveAspectRatio=True, mask='auto')
                imagenes_mostradas += 1
            except Exception:
                c.setFont("Helvetica", 8)
                c.setFillColor(HexColor("#ef4444"))
                c.drawString(315, y+100, "Error cargando mapa")
        
        # Si no se encontró el mapa de calor, mostrar mensaje
        if imagenes_mostradas == 1 and not (imagen_mapa and os.path.exists(imagen_mapa)):
            c.setFont("Helvetica", 9)
            c.setFillColor(HexColor("#9ca3af"))
            c.drawCentredString(3*w/4 - 20, y+100, "(Mapa de calor no disponible)")
        
        # ===================================
        # SECCIÓN DE MEDICIONES
        # ===================================
        y -= 50
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "MEDICIONES REALIZADAS:")
        c.setStrokeColor(HexColor("#0f172a"))
        c.line(50, y-3, 550, y-3)
        
        y -= 25
        c.setFont("Helvetica", 10)
        
        if informe[6]:  # Si hay mediciones en la BD
            try:
                meds = json.loads(informe[6])
                if meds:
                    # Separar por lado, asegurándonos de que soporte la nueva variable 'valor_mm' (o 'valor_cm' de versiones viejas)
                    izq = [m for m in meds if m.get('lado') == 'IZQ' and ('valor_mm' in m or 'valor_cm' in m)]
                    der = [m for m in meds if m.get('lado') == 'DER' and ('valor_mm' in m or 'valor_cm' in m)]
                    
                    # Encabezados
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(60, y, "PIE IZQUIERDO")
                    c.drawString(320, y, "PIE DERECHO")
                    y -= 18
                    
                    # Mediciones
                    c.setFont("Helvetica", 9)
                    max_items = max(len(izq), len(der))
                    
                    for i in range(max_items):
                        if i < len(izq):
                            valor = izq[i].get('valor_mm', izq[i].get('valor_cm', 0) * 10)
                            c.drawString(60, y-(i*14), f"• {izq[i]['tipo']}: {valor:.1f} mm")
                        if i < len(der):
                            valor = der[i].get('valor_mm', der[i].get('valor_cm', 0) * 10)
                            c.drawString(320, y-(i*14), f"• {der[i]['tipo']}: {valor:.1f} mm")
                    
                    y -= (max_items * 14) + 15
                else:
                    c.setFont("Helvetica", 9)
                    c.setFillColor(HexColor("#6b7280"))
                    c.drawString(60, y, "No se realizaron mediciones automáticas")
                    y -= 20
            except Exception:
                c.setFont("Helvetica", 9)
                c.setFillColor(HexColor("#ef4444"))
                c.drawString(60, y, f"Error al cargar mediciones")
                y -= 20
        else:
            c.setFont("Helvetica", 9)
            c.setFillColor(HexColor("#6b7280"))
            c.drawString(60, y, "No se registraron mediciones")
            y -= 20
        
        # ===================================
        # SECCIÓN DE DIAGNÓSTICO
        # ===================================
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "DIAGNÓSTICO Y OBSERVACIONES:")
        c.setStrokeColor(HexColor("#0f172a"))
        c.line(50, y-3, 550, y-3)
        
        y -= 20
        c.setFont("Helvetica", 10)
        
        if informe[4] and informe[4].strip():
            y = PDFManager._wrap_text(c, informe[4], 50, y, 500)
        else:
            c.setFillColor(HexColor("#6b7280"))
            c.drawString(50, y, "Sin observaciones registradas")
            y -= 20
        
        # ===================================
        # SECCIÓN DE RECOMENDACIONES
        # ===================================
        if informe[5] and informe[5].strip():
            y -= 15
            c.setFillColor(HexColor("#000000"))
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "RECOMENDACIONES:")
            c.setStrokeColor(HexColor("#0f172a"))
            c.line(50, y-3, 550, y-3)
            
            y -= 20
            c.setFont("Helvetica", 10)
            y = PDFManager._wrap_text(c, informe[5], 50, y, 500)
        
        # ===================================
        # FOOTER
        # ===================================
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#9ca3af"))
        c.drawCentredString(w/2, 30, f"Podoscopio Pro v3.0 - Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        c.save()
        return True