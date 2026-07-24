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

    soup_r = BeautifulSoup(html_r, 'html.parser')
    
    datos = {
        "rp222": {"texto": "Sin datos actualizados", "tipo": "warn"}
    }

    nombres_ruta = ['RP 222', 'RUTA 222', 'RP222', 'R.P. 222', 'RUTA PROVINCIAL 222']
    
    # 1. Buscamos por bloques (viñetas y párrafos) en lugar de romper todo con saltos de línea
    elementos = soup_r.find_all(['li', 'p'])
    
    for el in elementos:
        # Usamos espacio como separador para no romper las negritas
        linea = el.get_text(separator=' ', strip=True) 
        linea = re.sub(r'\s+', ' ', linea) # Limpiamos espacios dobles
        upper_linea = linea.upper()
        
        # 2. Verificamos que sea la ruta a Las Leñas
        if any(nombre in upper_linea for nombre in nombres_ruta) and "LAS LEÑAS" in upper_linea:
            texto_final = linea
            
            # 3. Corte inteligente: Si hay dos puntos, nos quedamos con la explicación de la derecha
            if ":" in texto_final:
                partes = texto_final.split(":", 1)
                if len(partes) > 1 and len(partes[1].strip()) > 5:
                    texto_final = partes[1].strip()
            
            # Emprolijamos para que empiece con mayúscula y termine con punto
            if texto_final:
                texto_final = texto_final[0].upper() + texto_final[1:]
            if not texto_final.endswith('.'): 
                texto_final += '.'
                
            datos["rp222"]["texto"] = texto_final
            break
            
    # 4. Asignación de colores (semáforo)
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
