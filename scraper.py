import cloudscraper
from bs4 import BeautifulSoup
import json
import requests
import re

def actualizar_rutas():
    url = 'https://prensa.mendoza.gob.ar/estado-de-las-rutas-en-mendoza-2/'
    proxy_url = f'https://api.codetabs.com/v1/proxy?quest={url}'
    
    try:
        response = requests.get(proxy_url, timeout=15)
        html = response.text
        if "estado-de-las-rutas" not in html.lower():
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            html = scraper.get(url).text
    except:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        html = scraper.get(url).text

    html = re.sub(r'<br\s*/?>', '\n', html)
    soup = BeautifulSoup(html, 'html.parser')
    
    texto_completo = soup.get_text(separator='\n', strip=True)
    lineas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
    
    # Diccionario donde guardamos el estado de TODAS las rutas
    datos = {
        "rp222": {"texto": "Sin datos actualizados", "tipo": "warn"},
        "rp52": {"texto": "Villavicencio – Uspallata", "tipo": "warn"},
        "rp13": {"texto": "Agua de Chilcas – Cerro 7 Colores", "tipo": "warn"},
        "rp220": {"texto": "Arroyo Blanco – Hotel Abandonado", "tipo": "warn"}
    }

    # Radar de palabras clave por ruta
    rutas_buscar = {
        "rp222": ['RP 222', 'RUTA 222', 'RP222', 'R.P. 222', 'RUTA PROVINCIAL 222'],
        "rp52": ['RP 52', 'RUTA 52', 'RP52', 'R.P. 52', 'RUTA PROVINCIAL 52'],
        "rp13": ['RP 13', 'RUTA 13', 'RP13', 'R.P. 13', 'RUTA PROVINCIAL 13'],
        "rp220": ['RP 220', 'RUTA 220', 'RP220', 'R.P. 220', 'RUTA PROVINCIAL 220']
    }
    
    for linea in lineas:
        upper_linea = linea.upper()
        
        # Detectamos si todo el renglón es sobre rutas intransitables (contexto general)
        tipo_linea = "warn"
        if any(p in upper_linea for p in ['CORTAD', 'INTRANSITABLE', 'CERRAD']):
            tipo_linea = "danger"
        elif any(p in upper_linea for p in ['CADENAS', 'PRECAUCI', 'HIELO']):
            tipo_linea = "warn"
        elif "TRANSITABLE" in upper_linea:
            tipo_linea = "ok"

        # Cortamos el renglón en oraciones
        oraciones = re.split(r'\.\s+', linea)
        
        # Buscamos cada ruta en las oraciones
        for key, aliases in rutas_buscar.items():
            for oracion in oraciones:
                upper_oracion = oracion.upper()
                if any(alias in upper_oracion for alias in aliases):
                    texto_final = oracion.strip()
                    if not texto_final.endswith('.'): texto_final += '.'
                    
                    # Determinamos el color: si la oración tiene aviso, lo usamos. Sino, usamos el del renglón.
                    tipo_oracion = tipo_linea
                    if any(p in upper_oracion for p in ['CORTAD', 'INTRANSITABLE', 'CERRAD']):
                        tipo_oracion = "danger"
                    elif any(p in upper_oracion for p in ['CADENAS', 'PRECAUCI', 'HIELO']):
                        tipo_oracion = "warn"
                    elif "TRANSITABLE" in upper_oracion:
                        tipo_oracion = "ok"
                        
                    datos[key] = {"texto": texto_final, "tipo": tipo_oracion}
                    break # Ya encontramos esta ruta, pasamos a la siguiente
    
    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    print("estado.json generado con éxito para todas las rutas.")

if __name__ == '__main__':
    actualizar_rutas()
