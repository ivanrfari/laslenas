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
    # 2. SCRAPER DE MEDIOS (A PRUEBA DE FALLOS)
    # ==========================================
    url_medios = 'https://laslenas.com/estado-pistas/medios/' 
    
    proxies = [
        f'https://api.allorigins.win/raw?url={url_medios}',
        f'https://api.codetabs.com/v1/proxy?quest={url_medios}'
    ]
    
    html_m = ""
    for proxy in proxies:
        try:
            res = requests.get(proxy, timeout=15)
            # Solo consideramos éxito si trae la clase CSS exacta que me pasaste
            if "medios__row" in res.text:
                html_m = res.text
                break
        except:
            continue
            
    if not html_m:
        try:
            scraper_m = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            res_m = scraper_m.get(url_medios)
            if "medios__row" in res_m.text:
                html_m = res_m.text
        except:
            pass

    medios_dict = {
        "eros1": {"nombre": "Eros 1", "aliases": ["eros 1", "eros i"], "tipo": "danger"},
        "eros2": {"nombre": "Eros 2", "aliases": ["eros 2", "eros ii"], "tipo": "danger"},
        "venus1": {"nombre": "Venus 1", "aliases": ["venus 1", "venus i"], "tipo": "danger"},
        "venus2": {"nombre": "Venus 2", "aliases": ["venus 2", "venus ii"], "tipo": "danger"},
        "neptuno": {"nombre": "Neptuno", "aliases": ["neptuno"], "tipo": "danger"},
        "marte": {"nombre": "Marte", "aliases": ["marte"], "tipo": "danger"},
        "minerva": {"nombre": "Minerva", "aliases": ["minerva"], "tipo": "danger"},
        "caris": {"nombre": "Caris", "aliases": ["caris"], "tipo": "danger"},
        "vulcano": {"nombre": "Vulcano", "aliases": ["vulcano"], "tipo": "danger"},
        "urano": {"nombre": "Urano", "aliases": ["urano"], "tipo": "danger"},
        "vesta": {"nombre": "Vesta", "aliases": ["vesta"], "tipo": "danger"}
    }

    if not html_m:
        datos["medios_error"] = True
    else:
        datos["medios_error"] = False
        soup_m = BeautifulSoup(html_m, 'html.parser')
        
        # ACA ESTÁ LA SOLUCIÓN: Agrupamos todo por la fila maestra
        filas = soup_m.find_all('div', class_=re.compile(r'medios__row'))
        
        if len(filas) == 0:
            datos["medios_error"] = True # Por si Las Leñas cambia la web de nuevo
        else:
            for fila in filas:
                medio_div = fila.find('div', class_=re.compile(r'medio__row--medio'))
                estado_div = fila.find('div', class_=re.compile(r'medio__row--estado'))
                
                if medio_div and estado_div:
                    # Le quitamos ABSOLUTAMENTE TODOS los espacios al nombre (Queda: "tkerosii")
                    texto_pista = medio_div.get_text(strip=True).lower().replace(" ", "")
                    
                    for key, val in medios_dict.items():
                        # Si encuentra el alias sin espacios en el texto sin espacios
                        if any(alias.replace(" ", "") in texto_pista for alias in val["aliases"]):
                            img = estado_div.find('img')
                            if img and 'src' in img.attrs:
                                src = img['src'].lower()
                                if 'abierta' in src or 'abierto' in src:
                                    val["tipo"] = "ok"
                                elif 'condicional' in src:
                                    val["tipo"] = "warn"
                                else:
                                    val["tipo"] = "danger"
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
