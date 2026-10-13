"""
Archivo: main.py
Ruta relativa: ./main.py

Descripción:
    Script principal de orquestación (CLI) para el proyecto Sudoku Solver Automation.
    Este archivo coordina la ejecución secuencial de todas las fases del pipeline:
        1. Captura de pantalla de la web.
        2. Detección y recorte del tablero mediante visión artificial.
        3. Reconocimiento Óptico de Caracteres (OCR) de las celdas.
        4. Validación lógica de la matriz extraída.
        5. Resolución matemática del puzzle mediante Backtracking.
    
    Al finalizar, calcula el tiempo total de ejecución y guarda todo el estado
    y los resultados en un archivo JSON local emparejado con la imagen capturada.

Uso:
    $ python main.py
"""

import sys
import os
import time

# Utilidades transversales
from utils.logger import logger
from utils.state_manager import inicializar_estado, guardar_estado

# Módulos del pipeline
from module.captura import capturar_tablero_sudoku
from module.deteccion import procesar_tablero
from module.reconocimiento import extraer_numeros
from module.validacion import validar_matriz
from module.solucionador import resolver_sudoku

def main():
    """
    Función principal que ejecuta el flujo de trabajo automatizado para resolver el Sudoku.
    Maneja la inicialización del estado, la invocación de cada fase con su respectivo
    control de errores, y el guardado final del reporte en formato JSON.
    """
    logger.info("==============================================")
    logger.info("Iniciando ejecución de Sudoku Solver Automation")
    logger.info("==============================================")

    # Registro del tiempo para medir la duración total del proceso
    tiempo_inicio_global = time.time()
    
    # Inicialización del diccionario que actuará como payload/estado a lo largo del pipeline
    estado = inicializar_estado()

    # ---------------------------------------------------------
    # FASE 1: Captura Web
    # ---------------------------------------------------------
    logger.info("Fase 1: Extracción de imagen del tablero web...")
    if not capturar_tablero_sudoku(estado):
        logger.error("Fallo en captura. Abortando.")
        sys.exit(1)

    # ---------------------------------------------------------
    # FASE 2: Visión Artificial y Recorte
    # ---------------------------------------------------------
    logger.info("Fase 2: Procesamiento visual del tablero...")
    if not procesar_tablero(estado):
        logger.error("Fallo en la detección del tablero. Abortando.")
        sys.exit(1)
        
    # ---------------------------------------------------------
    # FASE 3: OCR y Digitalización
    # ---------------------------------------------------------
    logger.info("Fase 3: Reconocimiento de dígitos (OCR)...")
    if not extraer_numeros(estado):
        logger.error("Fallo durante la extracción de texto OCR. Abortando.")
        sys.exit(1)

    # ---------------------------------------------------------
    # FASE 4: Validación Lógica
    # ---------------------------------------------------------
    logger.info("Fase 4: Validación de reglas lógicas...")
    if not validar_matriz(estado):
        logger.error("La matriz extraída es inválida. Abortando.")
        sys.exit(1)

    # ---------------------------------------------------------
    # FASE 5: Resolución y Cálculo
    # ---------------------------------------------------------
    logger.info("Fase 5: Resolviendo el puzzle...")
    if resolver_sudoku(estado):
        logger.info("Mostrando solución final:")
        for fila in estado["datos_sudoku"]["matriz_resuelta"]:
            logger.debug(str(fila))

    # ---------------------------------------------------------
    # Cierre y Generación de Reporte
    # ---------------------------------------------------------
    # Calcular tiempo total acumulado
    tiempo_fin_global = time.time()
    estado["tiempos"]["tiempo_total_segundos"] = round(tiempo_fin_global - tiempo_inicio_global, 2)

    # Nombrar y guardar JSON final vinculándolo al nombre de la imagen base generada
    nombre_base = os.path.basename(estado["metadatos"]["imagen_path"])
    nombre_json = "estado_" + nombre_base.replace(".png", ".json")
    guardar_estado(estado, nombre_json)
    
    logger.info(f"Pipeline completado. Estado consolidado guardado en: {nombre_json}")

if __name__ == "__main__":
    main()