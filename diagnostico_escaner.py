"""
SCRIPT DE DIAGNÓSTICO - Podoscopio Pro
Verifica qué escáneres detecta Windows
"""

import win32com.client

print("\n" + "="*60)
print("DIAGNÓSTICO DE ESCÁNERES - PODOSCOPIO PRO")
print("="*60 + "\n")

try:
    print("Inicializando WIA (Windows Image Acquisition)...")
    mgr = win32com.client.Dispatch("WIA.DeviceManager")
    
    count = mgr.DeviceInfos.Count
    print(f"\n✓ WIA inicializado correctamente")
    print(f"✓ Dispositivos detectados: {count}\n")
    
    if count == 0:
        print("⚠️  NO SE DETECTARON ESCÁNERES")
        print("\nPosibles causas:")
        print("  1. El escáner está apagado")
        print("  2. El escáner WiFi no está en la misma red")
        print("  3. Windows no reconoce el escáner WiFi (común)")
        print("  4. Faltan drivers del fabricante")
        print("\nSOLUCIÓN PARA CANON G3100 WiFi:")
        print("  → Usa IJ Scan Utility para escanear")
        print("  → Luego usa el botón 'CARGAR' en el Podoscopio")
    else:
        print(f"{'='*60}")
        print("ESCÁNERES DETECTADOS:")
        print(f"{'='*60}\n")
        
        for i in range(1, count + 1):
            print(f"[Escáner #{i}]")
            print("-" * 40)
            
            device_info = mgr.DeviceInfos(i)
            
            try:
                # Intentar obtener propiedades
                props = device_info.Properties
                
                print(f"  Propiedades disponibles: {props.Count}")
                
                # Propiedades comunes
                nombres_props = [
                    "Name", "Manufacturer", "Description", 
                    "Type", "Port", "Server", "RemoteDevID"
                ]
                
                for prop_name in nombres_props:
                    try:
                        valor = device_info.Properties(prop_name).Value
                        print(f"  {prop_name}: {valor}")
                    except:
                        pass
                
                print()
                
                # Intentar conectar al dispositivo
                try:
                    print("  Intentando conectar al dispositivo...")
                    device = device_info.Connect()
                    print("  ✓ Conexión exitosa")
                    
                    # Ver items disponibles
                    items_count = device.Items.Count
                    print(f"  Items disponibles: {items_count}")
                    
                    if items_count > 0:
                        print("  ✓ Este escáner está listo para usar")
                    
                except Exception as e:
                    print(f"  ✗ No se pudo conectar: {e}")
                
            except Exception as e:
                print(f"  ✗ Error obteniendo propiedades: {e}")
            
            print()
        
        print(f"{'='*60}\n")
    
    print("\nRECOMENDACIÓN:")
    print("-" * 60)
    if count > 0:
        print("✓ Hay escáneres detectados")
        print("✓ Puedes usar el botón 'ESCANEAR' del Podoscopio")
    else:
        print("✗ No hay escáneres detectados por Windows")
        print("→ Para escáneres WiFi: usa el software del fabricante")
        print("→ Luego usa el botón 'CARGAR' en el Podoscopio")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nPosibles soluciones:")
    print("  1. Instala: pip install pywin32")
    print("  2. Ejecuta como administrador")
    print("  3. Reinstala drivers del escáner")

print("\n" + "="*60)
print("FIN DEL DIAGNÓSTICO")
print("="*60 + "\n")

input("Presiona ENTER para cerrar...")
