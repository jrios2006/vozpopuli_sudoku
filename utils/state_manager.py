"""
Archivo: utils/state_manager.py
Ruta relativa: ./utils/state_manager.py

Descripción:
    Módulo de gestión de estado del pipeline.
    
    Provee la estructura de datos central (en formato de diccionario/JSON) 
    que viaja a través de todos los módulos del proyecto (captura, detección, 
    OCR, validación y resolución). 
    
    Este enfoque permite:
      - Desacoplar los módulos (cada uno solo lee y escribe en el estado).
      - Mantener una trazabilidad completa de los tiempos y posibles errores.
      - Generar evidencias en disco (archivos JSON) emparejadas con las imágenes.
"""

import json
import os
from datetime import datetime

def inicializar_estado():
    """
    Genera y devuelve la estructura base del JSON (payload) que recorrerá 
    todo el pipeline de ejecución.
    
    Returns:
        dict: Diccionario estructurado en bloques lógicos (metadatos, tiempos, 
              procesamiento y datos_sudoku) con valores iniciales por defecto.
    """
    return {
        "metadatos": {
            "fecha_captura": datetime.now().isoformat(),
            "estado_captura": "PENDIENTE",
            "mensaje_error": None,
            "imagen_path": None
        },
        "tiempos": {
            "fase_captura_segundos": 0.0,
            "fase_deteccion_segundos": 0.0,
            "fase_ocr_segundos": 0.0,
            "fase_resolucion_segundos": 0.0,
            "tiempo_total_segundos": 0.0
        },
        "procesamiento": {
            "tablero_detectado": False,
            "celdas_extraidas": 0,
            "nivel_confianza_ocr": 0.0
        },
        "datos_sudoku": {
            "matriz_inicial": [],
            "matriz_resuelta": [],
            "es_valido": False,
            "resuelto": False
        }
    }

def guardar_estado(estado, filepath="estado_actual.json"):
    """
    Vuelca el diccionario de estado actual en un archivo de texto con formato JSON.
    Se utiliza para persistir las evidencias al final de una ejecución.
    
    Args:
        estado (dict): El diccionario con los datos del proceso.
        filepath (str): Ruta y nombre del archivo de destino. Por defecto 'estado_actual.json'.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        # indent=4 formatea el JSON para que sea legible por humanos
        # ensure_ascii=False respeta los caracteres especiales (ej. acentos en mensajes de error)
        json.dump(estado, f, indent=4, ensure_ascii=False)

def cargar_estado(filepath="estado_actual.json"):
    """
    Lee un archivo JSON desde el disco y lo convierte de nuevo en un diccionario de Python.
    Útil si se desea desarrollar un módulo que reanude un proceso fallido o procese
    JSONs generados anteriormente.
    
    Args:
        filepath (str): Ruta del archivo JSON a leer.
        
    Returns:
        dict o None: El diccionario con el estado si el archivo existe, 
                     o None si no se encuentra la ruta.
    """
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None