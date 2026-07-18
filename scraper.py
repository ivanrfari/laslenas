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

    # Reemplazamos los saltos de línea HTML por texto real
    html = re.sub(r'<br\s*/?>', '\n', html)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extraemos el texto separando todos los bloques con \n
    texto_completo = soup.get_text(separator='\n', strip=True)
    
    # Separamos todo el documento línea por línea
    lineas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
    
    estado_rp222 = "No se encontró información de la ruta en el último reporte oficial."
    estado_tipo = "warn"
    
    nombres_ruta = ['RP 222', 'RUTA 222', 'RP222', 'R.P. 222', 'RUTA PROVINCIAL 222']
    
    for linea in lineas:
        upper_linea = linea.upper()
        if any(nombre in upper_linea for nombre in nombres_ruta):
            if len(linea) > 15:
                # Si el gobierno pegó muchas rutas en la misma línea, cortamos por oración (puntos)
                if ". " in linea or "RUTA" in linea[15:].upper():
                    oraciones = re.split(r'\.\s+', linea)
                    for oracion in oraciones:
                        if any(n in oracion.upper() for n in nombres_ruta):
                            estado_rp222 = oracion.strip()
                            # Le volvemos a poner el punto final si se lo sacó
                            if not estado_rp222.endswith('.'):
                                estado_rp222 += '.'
                            break
                else:
                    estado_rp222 = linea
                break
    
    # Asignación de colores y alertas automáticas
    texto_upper = estado_rp222.upper()
    if any(palabra in texto_upper for palabra in ['CORTAD', 'INTRANSITABLE', 'CERRAD']):
        estado_tipo = "danger"
    elif any(palabra in texto_upper for palabra in ['CADENAS', 'PRECAUCI', 'HIELO']):
        estado_tipo = "warn"
    elif "TRANSITABLE" in texto_upper:
        estado_tipo = "ok"
        
    datos = {
        "rp222": {
            "texto": estado_rp222,
            "tipo": estado_tipo
        }
    }
    
    # Guardamos el archivito que luego va a leer tu página web
    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    print("estado.json generado con éxito.")
    print(f"Texto extraído: {estado_rp222}")

if __name__ == '__main__':
    actualizar_rutas()
