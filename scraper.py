import cloudscraper
from bs4 import BeautifulSoup
import json
import requests
import re

def actualizar_rutas():
    # ==========================================
    # 1. SCRAPER DE RUTAS (Vialidad)
    # ==========================================
    url_rutas = 'https://prensa.mendoza.gob.ar/estado-de-las-rutas-en-mendoza-2/'
    proxy_rutas = f'https://api.codetabs.com/v1/proxy?quest={url_rutas}'
    
    try:
        response = requests.get(proxy_rutas, timeout=15)
        html_r = response.text
        if "estado-de-las-rutas" not in html_r.lower():
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            html_r = scraper.get(url_rutas).text
    except:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        html_r = scraper.get(url_rutas).text

    html_r = re.sub(r'<br\s*/?>', '\n', html_r)
    soup_r = BeautifulSoup(html_r, 'html.parser')
    
    texto_completo = soup_r.get_text(separator='\n', strip=True)
    lineas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
    
    datos = {
        "rp222": {"texto": "Sin datos actualizados", "tipo": "warn"},
        "rp52": {"texto": "Villavicencio – Uspallata", "tipo": "warn"},
        "rp13": {"texto": "Agua de Chilcas – Cerro 7 Colores", "tipo": "warn"},
        "rp220": {"texto": "Arroyo Blanco – Hotel Abandonado", "tipo": "warn"}
    }

    rutas_buscar = {
        "rp222": ['RP 222', 'RUTA 222', 'RP222', 'R.P. 222', 'RUTA PROVINCIAL 222'],
        "rp52": ['RP 52', 'RUTA 52', 'RP52', 'R.P. 52', 'RUTA PROVINCIAL 52'],
        "rp13": ['RP 13', 'RUTA 13', 'RP13', 'R.P. 13', 'RUTA PROVINCIAL 13'],
        "rp220": ['RP 220', 'RUTA 220', 'RP220', 'R.P. 220', 'RUTA PROVINCIAL 220']
    }
    
    for linea in lineas:
        upper_linea = linea.upper()
        
        tipo_linea = "warn"
        if any(p in upper_linea for p in ['CORTAD', 'INTRANSITABLE', 'CERRAD']):
            tipo_linea = "danger"
        elif any(p in upper_linea for p in ['CADENAS', 'PRECAUCI', 'HIELO']):
            tipo_linea = "warn"
        elif "TRANSITABLE" in upper_linea:
            tipo_linea = "ok"

        oraciones = re.split(r'\.\s+', linea)
        
        for key, aliases in rutas_buscar.items():
            for oracion in oraciones:
                upper_oracion = oracion.upper()
                if any(alias in upper_oracion for alias in aliases):
                    texto_final = oracion.strip()
                    if not texto_final.endswith('.'): texto_final += '.'
                    
                    tipo_oracion = tipo_linea
                    if any(p in upper_oracion for p in ['CORTAD', 'INTRANSITABLE', 'CERRAD']):
                        tipo_oracion = "danger"
                    elif any(p in upper_oracion for p in ['CADENAS', 'PRECAUCI', 'HIELO']):
                        tipo_oracion = "warn"
                    elif "TRANSITABLE" in upper_oracion:
                        tipo_oracion = "ok"
                        
                    datos[key] = {"texto": texto_final, "tipo": tipo_oracion}
                    break 

    # ==========================================
    # 2. SCRAPER DE MEDIOS DE ELEVACIÓN
    # ==========================================
    # URL oficial de estado de montaña de Las Leñas
    url_medios = 'https://laslenas.com/estado-de-la-montana/' 
    proxy_medios = f'https://api.codetabs.com/v1/proxy?quest={url_medios}'
    
    medios_dict = {
        "eros": {"nombre": "Eros", "estado": "Sin datos", "tipo": "warn"},
        "venus": {"nombre": "Venus", "estado": "Sin datos", "tipo": "warn"},
        "neptuno": {"nombre": "Neptuno", "estado": "Sin datos", "tipo": "warn"},
        "marte": {"nombre": "Marte", "estado": "Sin datos", "tipo": "warn"},
        "minerva": {"nombre": "Minerva", "estado": "Sin datos", "tipo": "warn"},
        "caris": {"nombre": "Caris", "estado": "Sin datos", "tipo": "warn"},
        "vulcano": {"nombre": "Vulcano", "estado": "Sin datos", "tipo": "warn"}
    }
    
    try:
        try:
            res_m = requests.get(proxy_medios, timeout=15)
            html_m = res_m.text
            if "leñas" not in html_m.lower():
                raise Exception("Fallo de proxy")
        except:
            scraper_m = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            html_m = scraper_m.get(url_medios).text
            
        soup_m = BeautifulSoup(html_m, 'html.parser')
        
        # Buscar cada medio en el HTML
        for key, val in medios_dict.items():
            nombre_buscar = val["nombre"].upper()
            
            # Buscar el texto del medio
            elemento = soup_m.find(string=re.compile(nombre_buscar, re.IGNORECASE))
            if elemento:
                # Subimos un par de etiquetas en el HTML para leer si dice Abierto o Cerrado cerca del nombre
                padre = elemento.parent
                for _ in range(4): 
                    if padre:
                        texto_padre = padre.get_text(separator=' ', strip=True).upper()
                        if "ABIERTO" in texto_padre or "HABILITADO" in texto_padre:
                            val["estado"] = "Abierto"
                            val["tipo"] = "ok"
                            break
                        elif "CONDICIONAL" in texto_padre or "PREPARACI" in texto_padre:
                            val["estado"] = "Condicional"
                            val["tipo"] = "warn"
                            break
                        elif "CERRADO" in texto_padre:
                            val["estado"] = "Cerrado"
                            val["tipo"] = "danger"
                            break
                        padre = padre.parent
    except Exception as e:
        print(f"No se pudieron actualizar los medios: {e}")
        
    datos["medios"] = medios_dict

    # ==========================================
    # 3. GUARDAR JSON
    # ==========================================
    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    print("estado.json generado con éxito para rutas y medios.")

if __name__ == '__main__':
    actualizar_rutas()
