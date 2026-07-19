import cloudscraper
from bs4 import BeautifulSoup
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
    # 2. SCRAPER DE MEDIOS DE ELEVACIÓN
    # ==========================================
    url_medios = 'https://laslenas.com/estado-de-la-montana/' 
    proxy_medios = f'https://api.codetabs.com/v1/proxy?quest={url_medios}'
    
    # Agregamos "aliases" por si escriben los nombres con números romanos
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
                raise Exception("Fallo de proxy")
        except:
            scraper_m = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            html_m = scraper_m.get(url_medios).text
            
        soup_m = BeautifulSoup(html_m, 'html.parser')
        
        for key, val in medios_dict.items():
            encontrado = False
            for alias in val["aliases"]:
                if encontrado:
                    break
                
                # Buscamos el nombre ignorando mayúsculas y minúsculas
                elemento = soup_m.find(string=re.compile(alias, re.IGNORECASE))
                
                if elemento:
                    # Buscamos todo el bloque de la tabla o lista
                    padre = elemento.find_parent(['tr', 'li', 'div', 'ul', 'tbody'])
                    if padre:
                        html_padre = str(padre).lower()
                        # Detectamos palabras o clases de íconos que indiquen que está abierto
                        if any(pista in html_padre for pista in ['abierto', 'habilitado', 'check', 'verde', 'green', 'open', 'status-open']):
                            val["tipo"] = "ok"
                    encontrado = True
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
