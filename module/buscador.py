"""
Archivo: module/buscador.py
Ruta relativa: ./module/buscador.py

Descripción:
    Módulo de scraping (raspado web) para extraer dinámicamente las URLs 
    reales de los sudokus diarios embebidos en Vozpópuli.
    
    Navega a las páginas genéricas de dificultad, busca el iframe 
    proveído por AmuseLabs y devuelve un diccionario con los enlaces 
    directos listos para inyectarse en el pipeline de resolución.
"""

from playwright.sync_api import sync_playwright
from utils.logger import logger

def obtener_urls_del_dia():
    """
    Visita las páginas principales de juegos de Vozpópuli y extrae los 
    enlaces directos de los iframes de los sudokus.
    
    Returns:
        dict: Un diccionario donde las claves son las dificultades ('Fácil', 
              'Medio', 'Difícil') y los valores son las URLs directas de AmuseLabs.
    """
    urls_base = {
        "Fácil": "https://www.vozpopuli.com/juegos/sudoku-facil",
        "Medio": "https://www.vozpopuli.com/juegos/sudoku-medio",
        "Difícil": "https://www.vozpopuli.com/juegos/sudoku-dificil"
    }
    
    enlaces_encontrados = {}
    
    logger.info("Iniciando búsqueda de sudokus del día en Vozpópuli...")
    
    try:
        with sync_playwright() as p:
            # Ejecutamos el navegador de forma invisible
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for dificultad, url in urls_base.items():
                try:
                    logger.debug(f"Inspeccionando página: {url}")
                    page.goto(url, timeout=20000)
                    
                    # Buscar el primer iframe cuyo atributo src contenga 'amuselabs.com'
                    iframe_element = page.locator("iframe[src*='amuselabs.com']").first
                    
                    if iframe_element.count() > 0:
                        src = iframe_element.get_attribute("src")
                        
                        # A veces las URLs vienen como "//puzzleme...", aseguramos el protocolo
                        if src.startswith("//"):
                            src = "https:" + src
                            
                        enlaces_encontrados[dificultad] = src
                        logger.info(f"Enlace para Sudoku {dificultad} extraído exitosamente.")
                    else:
                        logger.warning(f"No se encontró iframe de AmuseLabs en la dificultad {dificultad}.")
                        
                except Exception as e:
                    logger.error(f"Error al inspeccionar la URL {dificultad}: {str(e)}")
                    
            browser.close()
            
    except Exception as e:
        logger.error(f"Error crítico en el buscador de URLs: {str(e)}")
        
    return enlaces_encontrados