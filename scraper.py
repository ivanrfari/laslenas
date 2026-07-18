import cloudscraper
from bs4 import BeautifulSoup
import json
import requests

def actualizar_rutas():
    url = 'https://prensa.mendoza.gob.ar/estado-de-las-rutas-en-mendoza-2/'
    
    # 1. Usamos CodeTabs para camuflar la IP de GitHub y evitar el bloqueo del gobierno
    proxy_url = f'https://api.codetabs.com/v1/proxy?quest={url}'
    
    try:
        # Intentamos entrar por el proxy
        response = requests.get(proxy_url, timeout=15)
        html = response.text
        
        # Si el proxy devuelve un error o página vacía, usamos el scraper nativo como Plan B
        if "estado-de-las-rutas" not in html.lower():
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
            html = scraper.get(url).text
    except:
        # Plan C si falla la conexión
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        html = scraper.get(url).text

    soup = BeautifulSoup(html, 'html.parser')
    
    estado_rp222 = "No se encontró información de la ruta en el último reporte oficial."
    estado_tipo = "warn"
    
    # Buscamos en TODOS los elementos (párrafos, listas, tablas, etc.)
    for element in soup.find_all(['p', 'li', 'td', 'div', 'span']):
        # Extraemos el texto separando los saltos de línea
        texto = element.get_text(separator=' ', strip=True)
        upper_texto = texto.upper()
        
        # Buscamos TODAS las formas en las que el gobierno suele escribir la ruta
        nombres_ruta = ['RP 222', 'RUTA 222', 'RP222', 'R.P. 222', 'RUTA PROVINCIAL 222']
        
        if any(nombre in upper_texto for nombre in nombres_ruta):
            # Nos aseguramos de que sea una oración descriptiva y no un botón suelto
            if len(texto) > 15:
                estado_rp222 = texto
                break
    
    # Asignación de alertas de colores
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
    
    # Guardar en JSON
    with open('estado.json', 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        
    print("estado.json generado con éxito.")

if __name__ == '__main__':
    actualizar_rutas()
