import cloudscraper
from bs4 import BeautifulSoup
import json
import requests
import re

def actualizar_rutas():
    # ==========================================
    # SCRAPER DE LA RP 222 (Vialidad)
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
    # GUARDAR JSON
    # ==========================================
    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    print("estado.json generado con éxito (Solo Rutas).")

if __name__ == '__main__':
    actualizar_rutas()
