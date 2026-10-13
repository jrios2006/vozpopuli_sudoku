"""
Archivo: module/reconocimiento.py
Ruta relativa: ./module/reconocimiento.py

Descripción:
    Módulo encargado del Reconocimiento Óptico de Caracteres (OCR).
    
    Toma la imagen plana y recortada del tablero de Sudoku y realiza las 
    siguientes operaciones de procesamiento:
      1. Binarización de la imagen (blanco y negro puro) para resaltar el texto.
      2. División matemática de la imagen en una cuadrícula de 9x9 (81 celdas).
      3. Recorte de márgenes internos en cada celda para aislar el número de las 
         líneas divisorias del tablero.
      4. Evaluación de píxeles para distinguir celdas vacías de celdas con contenido.
      5. Ejecución de Tesseract OCR configurado específicamente para leer un único 
         dígito del 1 al 9 por imagen.
         
    El resultado es la transformación de una imagen gráfica en una estructura de 
    datos numérica (matriz de listas) que se inyecta en el estado global.
"""

import cv2
import pytesseract
import time
import os
from utils.logger import logger

def extraer_numeros(estado):
    """
    Divide el tablero recortado en 81 celdas, limpia los bordes y utiliza el 
    motor OCR Tesseract para identificar los dígitos iniciales del puzle.
    Actualiza la clave 'matriz_inicial' dentro de la sección 'datos_sudoku' del estado.
    
    Args:
        estado (dict): Diccionario global que contiene el estado del pipeline.
                       Debe contener la ruta de la imagen original en 
                       'metadatos' -> 'imagen_path'.
                       
    Returns:
        bool: True si la extracción por OCR finaliza correctamente, False si 
              ocurre un error de lectura o no se encuentra el archivo de imagen.
    """
    tiempo_inicio = time.time()
    
    # Recuperar la ruta base y derivar la ruta de la imagen recortada
    imagen_path = estado["metadatos"].get("imagen_path")
    if not imagen_path:
        logger.error("No hay imagen base en el estado para el OCR.")
        return False
        
    ruta_recorte = imagen_path.replace(".png", "_recortado.png")
    
    if not os.path.exists(ruta_recorte):
        logger.error(f"No se encontró la imagen recortada: {ruta_recorte}")
        return False
        
    try:
        logger.info("Iniciando fase de OCR sobre el tablero recortado...")
        
        # Leer imagen en escala de grises
        img = cv2.imread(ruta_recorte, cv2.IMREAD_GRAYSCALE)
        
        # Binarizar (Invertida: texto blanco, fondo negro) para detectar mejor si hay contenido.
        # Se usa el método de Otsu para encontrar el umbral óptimo de forma automática.
        _, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        
        # Calcular las dimensiones matemáticas de cada celda
        alto, ancho = img_bin.shape
        paso_y = alto // 9
        paso_x = ancho // 9
        
        matriz = []
        
        # Configuración estricta de Tesseract: 
        # --psm 10 : Tratar la imagen como un solo carácter.
        # -c tessedit_char_whitelist=123456789 : Limitar el reconocimiento solo a dígitos válidos.
        config_tesseract = '--psm 10 -c tessedit_char_whitelist=123456789'
        
        # Recorrer las 81 celdas
        for i in range(9):
            fila = []
            for j in range(9):
                # Extraer el fragmento de imagen correspondiente a la celda actual
                y_inicio, y_fin = i * paso_y, (i + 1) * paso_y
                x_inicio, x_fin = j * paso_x, (j + 1) * paso_x
                celda = img_bin[y_inicio:y_fin, x_inicio:x_fin]
                
                # Quitar un margen del 15% por cada lado para eliminar el ruido de 
                # los bordes negros o líneas de la rejilla
                m_y, m_x = int(paso_y * 0.15), int(paso_x * 0.15)
                celda_recortada = celda[m_y:-m_y, m_x:-m_x]
                
                # Contar píxeles blancos (que representan la tinta del número debido a la inversión)
                pixeles_blancos = cv2.countNonZero(celda_recortada)
                
                # Si hay pocos píxeles blancos, consideramos que la celda está vacía (representado con 0)
                if pixeles_blancos < 50:
                    fila.append(0)
                else:
                    # Invertir de nuevo para Tesseract (funciona mejor con texto negro sobre fondo blanco)
                    celda_ocr = cv2.bitwise_not(celda_recortada)
                    texto = pytesseract.image_to_string(celda_ocr, config=config_tesseract).strip()
                    
                    if texto.isdigit():
                        fila.append(int(texto[0])) # Tomamos solo el primer carácter por seguridad
                    else:
                        fila.append(0)  # Failsafe: si lee basura, se asume vacía
            matriz.append(fila)
        
        # Actualizar la matriz resultante en el estado JSON
        estado["datos_sudoku"]["matriz_inicial"] = matriz
        
        # Calcular y registrar el tiempo invertido en la fase OCR
        tiempo_fin = time.time()
        estado["tiempos"]["fase_ocr_segundos"] = round(tiempo_fin - tiempo_inicio, 2)
        
        logger.info(f"Fase de OCR completada en {estado['tiempos']['fase_ocr_segundos']}s.")
        return True
        
    except Exception as e:
        estado["metadatos"]["mensaje_error"] = f"Error OCR: {str(e)}"
        logger.error(f"Error durante el OCR: {str(e)}")
        return False