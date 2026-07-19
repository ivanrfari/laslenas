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
            raise Exception()
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
    # 2. SCRAPER ANTI-BLOQUEOS (Medios Las Leñas)
    # ==========================================
    url_medios = 'https://laslenas.com/estado-pistas/medios/' 
    
    # Lista de proxies (puentes) para saltar a Cloudflare
    proxies = [
        f'https://api.allorigins.win/raw?url={url_medios}',
        f'https://api.codetabs.com/v1/proxy?quest={url_medios}'
    ]
    
    html_m = ""
    # Intentamos primero con los puentes
    for proxy in proxies:
        try:
            res = requests.get(proxy, timeout=15)
            # Solo consideramos que funcionó si la página nombra al medio "Eros"
            if "eros" in res.text.lower():
                html_m = res.text
                break
        except:
            continue
            
    # Si los puentes fallan, intentamos directo con Cloudscraper
    if not html_m:
        try:
            scraper_m = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            res_m = scraper_m.get(url_medios)
            if "eros" in res_m.text.lower():
                html_m = res_m.text
        except:
            pass

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

    if not html_m:
        # EL ROBOT FUE BLOQUEADO. No inventamos datos.
        datos["medios_error"] = True
    else:
        # TENEMOS LA PÁGINA. Leemos los datos.
        datos["medios_error"] = False
        soup_m = BeautifulSoup(html_m, 'html.parser')
        
        claves_ok = ['abierto', 'habilitado', 'open', 'status-open', 'bg-green', 'text-green', 'check', 'fa-check', '✅', '✔', 'abierto.png', 'verde', 'dot-green']
        
        for key, val in medios_dict.items():
            for alias in val["aliases"]:
                nodos_texto = soup_m.find_all(string=re.compile(rf'\b{alias}\b', re.IGNORECASE))
                encontrado = False
                
                for nodo in nodos_texto:
                    contenedor = nodo.find_parent(['tr', 'li', 'div', 'td'])
                    if contenedor:
                        # Revisamos la caja HTML y sus contenedores cercanos
                        html_contenedor = str(contenedor).lower()
                        if contenedor.parent:
                            html_contenedor += str(contenedor.parent).lower()
                            
                        if any(pista in html_contenedor for pista in claves_ok):
                            val["tipo"] = "ok"
                            encontrado = True
                            break
                if encontrado:
                    break 
                    
    datos["medios"] = medios_dict

    # ==========================================
    # 3. GUARDAR JSON
    # ==========================================
    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    print("estado.json generado con éxito.")

if __name__ == '__main__':
    actualizar_rutas()
