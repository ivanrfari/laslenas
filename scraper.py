import cloudscraper
from bs4 import BeautifulSoup
import json
import requests
import re

def actualizar_rutas():
    # ... (El código de la Ruta 222 es el mismo de antes, lo dejo igual para ahorrarte scroll) ...
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
    
    datos = {"rp222": {"texto": "Sin datos actualizados", "tipo": "warn"}}
    nombres_ruta = ['RP 222', 'RUTA 222', 'RP222', 'R.P. 222', 'RUTA PROVINCIAL 222']
    
    for linea in lineas:
        upper_linea = linea.upper()
        if any(nombre in upper_linea for nombre in nombres_ruta):
            datos["rp222"]["texto"] = linea
            break
            
    texto_upper = datos["rp222"]["texto"].upper()
    if any(palabra in texto_upper for palabra in ['CORTAD', 'INTRANSITABLE', 'CERRAD']): datos["rp222"]["tipo"] = "danger"
    elif any(palabra in texto_upper for palabra in ['CADENAS', 'PRECAUCI', 'HIELO']): datos["rp222"]["tipo"] = "warn"
    elif "TRANSITABLE" in texto_upper: datos["rp222"]["tipo"] = "ok"

    # ==========================================
    # 2. SCRAPER DE MEDIOS (Detector mejorado)
    # ==========================================
    url_medios = 'https://laslenas.com/estado-pistas/medios/' 
    proxies = [f'https://api.allorigins.win/raw?url={url_medios}', f'https://api.codetabs.com/v1/proxy?quest={url_medios}']
    
    html_m = ""
    for proxy in proxies:
        try:
            res = requests.get(proxy, timeout=15)
            if "medios__row" in res.text:
                html_m = res.text
                break
        except: continue
            
    # Definimos los medios con alias que cubren el prefijo "tk/ts" y los romanos
    medios_dict = {
        "eros1": {"nombre": "Eros 1", "aliases": ["eros1", "erosi"], "tipo": "danger"},
        "eros2": {"nombre": "Eros 2", "aliases": ["eros2", "erosii"], "tipo": "danger"},
        "venus1": {"nombre": "Venus 1", "aliases": ["venus1", "venusi"], "tipo": "danger"},
        "venus2": {"nombre": "Venus 2", "aliases": ["venus2", "venusii"], "tipo": "danger"},
        "neptuno": {"nombre": "Neptuno", "aliases": ["neptuno"], "tipo": "danger"},
        "marte": {"nombre": "Marte", "aliases": ["marte"], "tipo": "danger"},
        "minerva": {"nombre": "Minerva", "aliases": ["minerva"], "tipo": "danger"},
        "caris": {"nombre": "Caris", "aliases": ["caris"], "tipo": "danger"},
        "vulcano": {"nombre": "Vulcano", "aliases": ["vulcano"], "tipo": "danger"},
        "urano": {"nombre": "Urano", "aliases": ["urano"], "tipo": "danger"},
        "vesta": {"nombre": "Vesta", "aliases": ["vesta"], "tipo": "danger"}
    }

    if html_m:
        soup_m = BeautifulSoup(html_m, 'html.parser')
        filas = soup_m.find_all('div', class_=re.compile(r'medios__row'))
        
        for fila in filas:
            medio_div = fila.find('div', class_=re.compile(r'medio__row--medio'))
            estado_div = fila.find('div', class_=re.compile(r'medio__row--estado'))
            
            if medio_div and estado_div:
                # Quitamos espacios y prefijos como "tk" o "ts" para que el match sea perfecto
                texto_pista = medio_div.get_text(strip=True).lower().replace(" ", "").replace("ts", "").replace("tk", "").replace("tele", "")
                
                for key, val in medios_dict.items():
                    # Buscamos si el alias está contenido en el nombre limpio
                    if any(alias in texto_pista for alias in val["aliases"]):
                        img = estado_div.find('img')
                        if img and 'src' in img.attrs:
                            src = img['src'].lower()
                            if 'abierta' in src or 'abierto' in src: val["tipo"] = "ok"
                            elif 'condicional' in src: val["tipo"] = "warn"
                            else: val["tipo"] = "danger"
                        break

    datos["medios"] = medios_dict
    datos["medios_error"] = not bool(html_m)

    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    actualizar_rutas()
