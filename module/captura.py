"""
Archivo: module/captura.py
Ruta relativa: ./module/captura.py

Descripción:
    Módulo de automatización web y extracción de imágenes.
    
    Utiliza la librería Playwright para controlar un navegador Chromium de 
    forma automatizada (típicamente en modo 'headless' o invisible). 
    Su objetivo principal es navegar a la URL proporcionada (ya sea desde la 
    configuración o inyectada por la GUI), esperar a que los scripts de la 
    página rendericen el juego, y aislar el tablero tomando una captura de 
    pantalla del elemento interactivo (<canvas>).
    
    Esta imagen se guarda localmente con una marca de tiempo única para 
    alimentar la siguiente fase (Visión Artificial).
"""

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from utils.logger import load_config, logger

def capturar_tablero_sudoku(estado, url_dinamica=None):
    """
    Abre la URL objetivo, realiza la captura de pantalla del tablero y 
    actualiza el JSON de estado global con los resultados, tiempos de 
    ejecución y la ruta local de la evidencia generada.
    
    Args:
        estado (dict): Diccionario JSON con el estado global del proceso. 
                       Se actualizará in-place con metadatos y tiempos.
        url_dinamica (str, opcional): Permite inyectar una URL dinámicamente 
                                      desde la GUI. Si es None, recae en la URL 
                                      por defecto definida en config.json.
        
    Returns:
        bool: True si la captura y guardado de la imagen fue exitosa, 
              False en caso de error de red, timeout o fallo del navegador.
    """
    # Iniciar cronómetro de la fase
    tiempo_inicio = time.time()
    
    # Cargar configuraciones
    config = load_config()
    browser_config = config.get("browser", {})
    paths_config = config.get("paths", {})
    
    # Determinar la URL final: prioridad a la dinámica (GUI) sobre la estática (config)
    url = url_dinamica if url_dinamica else browser_config.get("url")
    
    # Guardar metadatos iniciales para trazabilidad
    estado["metadatos"]["url_origen"] = url
    estado["metadatos"]["fecha_captura"] = datetime.now().isoformat()
    
    headless = browser_config.get("headless", True)
    # Convertir timeout de segundos (config) a milisegundos (requerido por Playwright)
    timeout = browser_config.get("timeout_seconds", 15) * 1000
    
    # Preparar el directorio de salida
    images_dir = paths_config.get("images_dir", "imagenes")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
        logger.info(f"Carpeta de imágenes creada en: {images_dir}")

    # Generar nombre de archivo único basado en la fecha y hora de ejecución
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"sudoku_{timestamp_str}.png"
    output_path = os.path.join(images_dir, output_filename)
    
    logger.info(f"Iniciando navegador para capturar URL: {url}")

    try:
        # Iniciar sesión de automatización con Playwright
        with sync_playwright() as p:
            # Lanzar navegador Chromium (modo invisible o visible según config)
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            
            logger.debug("Navegando a la página del sudoku...")
            page.goto(url, timeout=timeout)
            
            # Margen de seguridad para permitir que scripts de terceros (AmuseLabs) 
            # dibujen el tablero interactivo en el DOM.
            logger.debug("Esperando a que el tablero interactivo se renderice...")
            time.sleep(4) 
            
            # Buscar el elemento <canvas> que suele contener el puzle
            canvas_locator = page.locator("canvas").first
            if canvas_locator.count() > 0:
                logger.info("Canvas detectado. Tomando captura enfocada en el elemento del juego...")
                canvas_locator.screenshot(path=output_path)
            else:
                logger.warning("No se encontró un canvas específico. Tomando captura de la vista general...")
                # Fallback: captura de pantalla completa de la vista actual
                page.screenshot(path=output_path, full_page=False)

            browser.close()
            
        # Calcular el tiempo transcurrido en la fase
        tiempo_fin = time.time()
        duracion = round(tiempo_fin - tiempo_inicio, 2)
            
        # Actualizar el estado JSON con éxito, ruta de evidencia y métricas
        estado["metadatos"]["estado_captura"] = "OK"
        estado["metadatos"]["imagen_path"] = output_path
        estado["tiempos"]["fase_captura_segundos"] = duracion
        
        logger.info(f"Captura de pantalla guardada con éxito en: {output_path} (Tiempo invertido: {duracion}s)")
        return True

    except Exception as e:
        # Calcular el tiempo transcurrido incluso en caso de error
        tiempo_fin = time.time()
        duracion = round(tiempo_fin - tiempo_inicio, 2)
        
        # Registrar el error en el estado global para su posterior revisión
        estado["metadatos"]["estado_captura"] = "ERROR"
        estado["metadatos"]["mensaje_error"] = str(e)
        estado["tiempos"]["fase_captura_segundos"] = duracion
        
        logger.error(f"Error crítico durante la captura web: {str(e)}")
        return False