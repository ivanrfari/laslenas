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
    # 2. SCRAPER DE MEDIOS (Con detector de romanos)
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
            if "neptuno" in res.text.lower():
                html_m = res.text
                break
        except:
            continue
            
    if not html_m:
        try:
            scraper_m = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            res_m = scraper_m.get(url_medios)
            if "neptuno" in res_m.text.lower():
                html_m = res_m.text
        except:
            pass

    # Incluimos los números romanos en los "aliases" para que no se le escape ninguno
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
        
        cajas_nombres = soup_m.find_all('div', class_=re.compile(r'medio__row--medio'))
        
        for caja in cajas_nombres:
            texto_pista = caja.get_text(strip=True).lower()
            
            for key, val in medios_dict.items():
                # Revisa si la caja contiene el nombre normal o el romano
                if any(alias in texto_pista or alias.replace(" ", "") in texto_pista for alias in val["aliases"]):
                    
                    caja_estado = caja.find_next_sibling('div', class_=re.compile(r'medio__row--estado'))
                    
                    if caja_estado:
                        imagen = caja_estado.find('img')
                        if imagen and 'src' in imagen.attrs:
                            link_imagen = imagen['src'].lower()
                            
                            if 'cerrada' in link_imagen:
                                val["tipo"] = "danger"
                            elif 'condicional' in link_imagen:
                                val["tipo"] = "warn"
                            else:
                                val["tipo"] = "ok"
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
