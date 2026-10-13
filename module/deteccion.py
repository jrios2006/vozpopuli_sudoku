"""
Archivo: module/deteccion.py
Ruta relativa: ./module/deteccion.py

Descripción:
    Módulo de procesamiento de imagen y visión artificial.
    
    Utiliza OpenCV para aislar el tablero de Sudoku del resto de la captura web.
    El flujo de procesamiento consiste en:
      1. Conversión a escala de grises y filtrado de ruido (Gaussian Blur).
      2. Binarización adaptativa para resaltar las líneas de la cuadrícula.
      3. Detección de contornos para encontrar el polígono de 4 lados más grande.
      4. Corrección de perspectiva (Warp Perspective) para "aplanar" la imagen 
         y recortarla, eliminando cualquier fondo o menú del navegador.
         
    Genera una nueva imagen terminada en '_recortado.png' que servirá como 
    base perfecta para el OCR en la siguiente fase.
"""

import cv2
import numpy as np
import time
import os
from utils.logger import logger

def ordenar_puntos(pts):
    """
    Ordena un conjunto de 4 coordenadas (puntos) de un polígono para garantizar 
    un orden consistente necesario para la transformación de perspectiva.
    
    El orden resultante siempre es: 
    1. Arriba-Izquierda (top-left)
    2. Arriba-Derecha (top-right)
    3. Abajo-Derecha (bottom-right)
    4. Abajo-Izquierda (bottom-left)
    
    Args:
        pts (numpy.ndarray): Matriz de 4x2 con las coordenadas (x, y) desordenadas.
        
    Returns:
        numpy.ndarray: Matriz de 4x2 con los puntos ordenados lógicamente.
    """
    rect = np.zeros((4, 2), dtype="float32")
    
    # La suma de las coordenadas (x + y):
    # - El punto Arriba-Izquierda tendrá la suma más pequeña.
    # - El punto Abajo-Derecha tendrá la suma más grande.
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # La diferencia de las coordenadas (y - x):
    # - El punto Arriba-Derecha tendrá la diferencia más pequeña.
    # - El punto Abajo-Izquierda tendrá la diferencia más grande.
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def procesar_tablero(estado):
    """
    Lee la imagen capturada referenciada en el estado, localiza matemáticamente 
    la cuadrícula del Sudoku, corrige su perspectiva y guarda el recorte resultante.
    
    Args:
        estado (dict): Diccionario global que contiene el estado del pipeline.
                       Debe incluir la ruta de la imagen original.
                       
    Returns:
        bool: True si el tablero es detectado y recortado con éxito, False en caso 
              de error (imagen no encontrada, contorno no detectado, etc.).
    """
    tiempo_inicio = time.time()
    imagen_path = estado["metadatos"].get("imagen_path")
    
    if not imagen_path or not os.path.exists(imagen_path):
        logger.error("No se encontró la ruta de la imagen para procesar.")
        return False

    try:
        logger.info(f"Procesando imagen: {imagen_path}")
        
        # 1. Carga y preprocesamiento de color a escala de grises
        img = cv2.imread(imagen_path)
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Reducción de ruido y umbralización para destacar líneas negras sobre fondo blanco
        desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)
        umbral = cv2.adaptiveThreshold(desenfoque, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)

        # 3. Búsqueda de todos los contornos externos en la imagen binarizada
        contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Ordenar contornos de mayor a menor área para encontrar el tablero rápidamente
        contornos = sorted(contornos, key=cv2.contourArea, reverse=True)

        tablero_contorno = None
        for c in contornos:
            perimetro = cv2.arcLength(c, True)
            # Aproximar el contorno a un polígono para suavizar bordes irregulares
            aproximacion = cv2.approxPolyDP(c, 0.02 * perimetro, True)
            
            # El tablero del Sudoku debe ser el polígono de 4 lados (cuadrado/rectángulo) más grande
            if len(aproximacion) == 4:
                tablero_contorno = aproximacion
                break

        if tablero_contorno is None:
            logger.error("No se detectó un tablero de 4 lados en la imagen.")
            return False

        # 4. Transformación de perspectiva (Warp Perspective)
        # Extraer y ordenar los vértices detectados
        pts = tablero_contorno.reshape(4, 2)
        rect = ordenar_puntos(pts)
        (tl, tr, br, bl) = rect

        # Calcular la anchura máxima del nuevo rectángulo (distancia entre esquinas inferiores o superiores)
        anchuraA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        anchuraB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_anchura = max(int(anchuraA), int(anchuraB))

        # Calcular la altura máxima del nuevo rectángulo (distancia entre esquinas laterales)
        alturaA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        alturaB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_altura = max(int(alturaA), int(alturaB))

        # Definir las coordenadas del rectángulo de destino (perfectamente plano y recto)
        dst = np.array([
            [0, 0],
            [max_anchura - 1, 0],
            [max_anchura - 1, max_altura - 1],
            [0, max_altura - 1]], dtype="float32")

        # Calcular la matriz de transformación y aplicarla a la imagen original en grises
        M = cv2.getPerspectiveTransform(rect, dst)
        warp = cv2.warpPerspective(gris, M, (max_anchura, max_altura))

        # 5. Guardar la evidencia fotográfica del tablero aislado
        ruta_recorte = imagen_path.replace(".png", "_recortado.png")
        cv2.imwrite(ruta_recorte, warp)
        logger.info(f"Tablero recortado guardado en: {ruta_recorte}")

        # 6. Actualizar las banderas lógicas del estado global
        estado["procesamiento"]["tablero_detectado"] = True
        estado["procesamiento"]["celdas_extraidas"] = 81
        
        tiempo_fin = time.time()
        estado["tiempos"]["fase_deteccion_segundos"] = round(tiempo_fin - tiempo_inicio, 2)
        
        logger.info(f"Fase de detección completada en {estado['tiempos']['fase_deteccion_segundos']}s.")
        return True

    except Exception as e:
        estado["metadatos"]["mensaje_error"] = str(e)
        logger.error(f"Error durante la detección: {str(e)}")
        return False