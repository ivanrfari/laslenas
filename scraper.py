import cloudscraper
from bs4 import BeautifulSoup
import json
import os

def actualizar_rutas():
    # Cloudscraper evita los bloqueos de bots y Cloudflare
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    url = 'https://prensa.mendoza.gob.ar/estado-de-las-rutas-en-mendoza-2/'
    
    try:
        html = scraper.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        
        estado_rp222 = "No se encontró información de la ruta en el último reporte oficial."
        estado_tipo = "warn"
        
        # Escaneo de elementos HTML buscando la ruta
        for element in soup.find_all(['p', 'li', 'div', 'span', 'strong']):
            texto = element.get_text(strip=True)
            if ('RP 222' in texto.upper() or 'RUTA 222' in texto.upper() or 'RP222' in texto.upper()) and len(texto) > 15:
                estado_rp222 = texto
                break
        
        # Asignación de colores/estados
        texto_upper = estado_rp222.upper()
        if any(palabra in texto_upper for palabra in ['CORTAD', 'INTRANSITABLE', 'CERRAD']):
            estado_tipo = "danger"
        elif any(palabra in texto_upper for palabra in ['CADENAS', 'PRECAUCI', 'HIELO']):
            estado_tipo = "warn"
        else:
            estado_tipo = "ok"
            
        datos = {
            "rp222": {
                "texto": estado_rp222,
                "tipo": estado_tipo
            }
        }
        
        # Guarda el JSON en el mismo directorio
        with open('estado.json', 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
            
        print("estado.json generado con éxito.")
    except Exception as e:
        print(f"Falla en la sincronización: {e}")

if __name__ == '__main__':
    actualizar_rutas()
