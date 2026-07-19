import cloudscraper
import json
import requests
import re

def actualizar_rutas():
    # ==========================================
    # 1. SCRAPER DE LA RP 222 (Vialidad)
    # ==========================================
    url_rutas = 'https://prensa.mendoza.gob.ar/estado-de-las-rutas-en-mendoza-2/'
    proxy_rutas = f'https://api.codetabs.com/v1/proxy?quest={url_rutas}'
    
    try:
        response = requests.get(proxy_rutas, timeout=15)
        html_r = response.text
        if "estado-de-las-rutas" not in html_r.lower():
            raise Exception()
    except:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        html_r = scraper.get(url_rutas).text

    # Limpiamos el HTML para leer el texto
    html_r = re.sub(r'<br\s*/?>', '\n', html_r)
    texto_completo = re.sub(r'<[^>]+>', '\n', html_r) # Quita todas las etiquetas ocultas
    
    lineas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
    
    datos = {
        "rp222": {"texto": "Sin datos actualizados", "tipo": "warn"}
    }

    nombres_ruta = ['RP 222', 'RUTA 222', 'RP222', 'R.P. 222', 'RUTA PROVINCIAL 222']
    
    for linea in lineas:
        upper_linea = linea.upper()
        if any(nombre in upper_linea for nombre in nombres_ruta):
            if len(linea) > 15:
                if ". " in linea or "RUTA" in linea[15:].upper():
                    oraciones = re.split(r'\.\s+', linea)
                    for oracion in oraciones:
                        if any(n in oracion.upper() for n in nombres_ruta):
                            texto_final = oracion.strip()
                            if not texto_final.endswith('.'): texto_final += '.'
                            datos["rp222"]["texto"] = texto_final
                            break
                else:
                    datos["rp222"]["texto"] = linea
                break
    
    texto_upper = datos["rp222"]["texto"].upper()
    if any(palabra in texto_upper for palabra in ['CORTAD', 'INTRANSITABLE', 'CERRAD']):
        datos["rp222"]["tipo"] = "danger"
    elif any(palabra in texto_upper for palabra in ['CADENAS', 'PRECAUCI', 'HIELO']):
        datos["rp222"]["tipo"] = "warn"
    elif "TRANSITABLE" in texto_upper:
        datos["rp222"]["tipo"] = "ok"

    # ==========================================
    # 2. SCRAPER INTELIGENTE DE MEDIOS
    # ==========================================
    url_medios = 'https://laslenas.com/estado-de-la-montana/' 
    proxy_medios = f'https://api.codetabs.com/v1/proxy?quest={url_medios}'
    
    medios_dict = {
        "eros1": {"nombre": "Eros 1", "aliases": ["Eros 1", "Eros I"], "tipo": "danger"},
        "eros2": {"nombre": "Eros 2", "aliases": ["Eros 2", "Eros II"], "tipo": "danger"},
        "venus1": {"nombre": "Venus 1", "aliases": ["Venus 1", "Venus I"], "tipo": "danger"},
        "venus2": {"nombre": "Venus 2", "aliases": ["Venus 2", "Venus II"], "tipo": "danger"},
        "neptuno": {"nombre": "Neptuno", "aliases": ["Neptuno"], "tipo": "danger"},
        "marte": {"nombre": "Marte", "aliases": ["Marte"], "tipo": "danger"},
        "minerva": {"nombre": "Minerva", "aliases": ["Minerva"], "tipo": "danger"},
        "caris": {"nombre": "Caris", "aliases": ["Caris"], "tipo": "danger"},
        "vulcano": {"nombre": "Vulcano", "aliases": ["Vulcano"], "tipo": "danger"},
        "urano": {"nombre": "Urano", "aliases": ["Urano"], "tipo": "danger"},
        "vesta": {"nombre": "Vesta", "aliases": ["Vesta"], "tipo": "danger"}
    }
    
    try:
        try:
            res_m = requests.get(proxy_medios, timeout=15)
            html_m = res_m.text
            if "leñas" not in html_m.lower():
                raise Exception()
        except:
            scraper_m = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            html_m = scraper_m.get(url_medios).text
            
        html_lower = html_m.lower()
        
        # Diccionario con todas las formas posibles de "Abierto" y "Cerrado" en el código
        keywords_ok = ['abierto', 'habilitado', 'check', 'verde', 'green', 'open', 'status-open', '✔', '✅', 'dot-green']
        keywords_danger = ['cerrado', 'deshabilitado', 'cruz', 'rojo', 'red', 'closed', 'status-closed', 'fa-times', '❌', 'dot-red']

        for key, val in medios_dict.items():
            for alias in val["aliases"]:
                idx = html_lower.find(alias.lower())
                
                if idx != -1:
                    # Si encuentra la telesilla, recorta un bloque del código a su alrededor
                    start = max(0, idx - 250)
                    end = min(len(html_lower), idx + 400)
                    window = html_lower[start:end]
                    
                    # Calcula el punto exacto donde está el nombre
                    center = idx - start
                    
                    # Mide qué tan cerca está una palabra de habilitado
                    dist_ok = 9999
                    for k in keywords_ok:
                        for match in re.finditer(re.escape(k), window):
                            d = abs(match.start() - center)
                            if d < dist_ok: dist_ok = d
                                
                    # Mide qué tan cerca está una palabra de cerrado
                    dist_danger = 9999
                    for k in keywords_danger:
                        for match in re.finditer(re.escape(k), window):
                            d = abs(match.start() - center)
                            if d < dist_danger: dist_danger = d
                                
                    # Compara distancias: la que esté más pegada al nombre de la pista, es el estado real.
                    if dist_ok < dist_danger:
                        val["tipo"] = "ok"
                    break
                    
    except Exception as e:
        print(f"Error escaneando medios: {e}")
        
    datos["medios"] = medios_dict

    # ==========================================
    # 3. GUARDAR JSON
    # ==========================================
    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    print("estado.json generado con éxito.")

if __name__ == '__main__':
    actualizar_rutas()
