"""
Archivo: module/inyeccion.py
Ruta relativa: ./module/inyeccion.py

Descripción:
    Módulo de automatización para escribir la solución directamente en la web.
    
    A través de Playwright, localiza los elementos HTML del tablero de AmuseLabs,
    hace clic secuencialmente en las celdas vacías y envía las pulsaciones de 
    teclado necesarias para completar el puzle.
"""

import time
from playwright.sync_api import sync_playwright
from utils.logger import load_config, logger

def inyectar_solucion(estado):
    """
    Abre un navegador visible, localiza las 81 celdas HTML del Sudoku y 
    teclea la solución en los huecos vacíos.
    
    Args:
        estado (dict): Estado global con la matriz inicial, la resuelta y la URL.
        
    Returns:
        bool: True si completó la escritura con éxito, False si hubo errores.
    """
    tiempo_inicio = time.time()
    
    if not estado["datos_sudoku"].get("resuelto", False):
        logger.error("No se puede inyectar la solución porque el sudoku no está resuelto.")
        return False

    url = estado["metadatos"].get("url_origen")
    matriz_inicial = estado["datos_sudoku"]["matriz_inicial"]
    matriz_resuelta = estado["datos_sudoku"]["matriz_resuelta"]
    
    config = load_config()
    timeout = config.get("browser", {}).get("timeout_seconds", 15) * 1000

    logger.info("Iniciando navegador para inyectar la solución web mediante DOM...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(url, timeout=timeout)
            
            logger.debug("Esperando dinámicamente a que los elementos HTML del tablero carguen...")
            
            # Esperamos hasta 15s a que aparezca al menos un contenedor de celda
            page.wait_for_selector(".pencil-letters-in-box", state="attached", timeout=15000)
            
            # Le damos 1 segundo de cortesía para que el JavaScript termine de armar el tablero
            time.sleep(1) 
            
            # Recopilamos todas las celdas del tablero
            celdas = page.locator(".pencil-letters-in-box")
            cantidad_celdas = celdas.count()
            
            if cantidad_celdas != 81:
                logger.error(f"Estructura inesperada: se encontraron {cantidad_celdas} celdas en lugar de 81.")
                browser.close()
                return False

            logger.info("Tablero HTML detectado correctamente. Iniciando inyección de teclas...")

            # El HTML indexa las 81 celdas de forma secuencial (0 a 80)
            indice = 0
            for i in range(9):
                for j in range(9):
                    # Solo interactuamos si la celda original estaba vacía
                    if matriz_inicial[i][j] == 0:
                        numero = str(matriz_resuelta[i][j])
                        
                        # Seleccionamos el elemento de la celda correspondiente
                        celda_actual = celdas.nth(indice)
                        
                        # Hacemos clic (Playwright pincha en el centro del elemento por defecto)
                        celda_actual.click()
                        
                        # Tecleamos el número
                        page.keyboard.press(numero)
                        
                        # Pausa mínima para imitar tecleo humano y evitar saturar la web
                        time.sleep(0.05)
                    
                    indice += 1 # Avanzamos el índice general sin importar si escribimos o no

            logger.info("¡Tablero completado con éxito en la web!")
            time.sleep(3) # Pausa final para que veas el mensaje de victoria
            browser.close()
            
            tiempo_fin = time.time()
            estado["tiempos"]["fase_inyeccion_segundos"] = round(tiempo_fin - tiempo_inicio, 2)
            estado["tiempos"]["tiempo_total_segundos"] = round(estado["tiempos"]["tiempo_total_segundos"] + estado["tiempos"]["fase_inyeccion_segundos"], 2)
            
            return True

    except Exception as e:
        logger.error(f"Error durante la inyección web: {str(e)}")
        return False