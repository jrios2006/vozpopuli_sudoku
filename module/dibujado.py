"""
Archivo: module/dibujado.py
Ruta relativa: ./module/dibujado.py

Descripción:
    Módulo encargado de la generación de la evidencia visual final.
    
    Toma la imagen del tablero previamente recortado (Fase 2), compara la 
    matriz inicial (Fase 3) con la matriz resuelta (Fase 5), y utiliza OpenCV 
    para dibujar únicamente los números calculados por el algoritmo sobre 
    las celdas que originalmente estaban vacías.
    
    El resultado es una nueva imagen guardada en disco que sirve para mostrarse 
    en la interfaz gráfica (GUI) o como comprobante del éxito del pipeline.
"""

import cv2
import os
from utils.logger import logger

def generar_imagen_solucion(estado):
    """
    Superpone los números de la solución matemática sobre la imagen fotográfica 
    del tablero original, guardando el resultado como una nueva imagen.
    
    Args:
        estado (dict): Diccionario global que contiene las rutas de las imágenes 
                       y las matrices 'matriz_inicial' y 'matriz_resuelta'.
                       
    Returns:
        bool: True si la imagen se genera y guarda correctamente, False si ocurre 
              un error o no se encuentra la imagen base.
    """
    try:
        # Construir la ruta esperada de la imagen recortada plana
        ruta_recorte = estado["metadatos"]["imagen_path"].replace(".png", "_recortado.png")
        if not os.path.exists(ruta_recorte):
            logger.error(f"No se encontró la imagen base para dibujar: {ruta_recorte}")
            return False

        # Cargar la imagen original en color
        img = cv2.imread(ruta_recorte)
        alto, ancho, _ = img.shape
        
        # Calcular el tamaño de cada celda matemática
        paso_y, paso_x = alto // 9, ancho // 9

        matriz_inicial = estado["datos_sudoku"]["matriz_inicial"]
        matriz_resuelta = estado["datos_sudoku"]["matriz_resuelta"]

        # Configuración de tipografía de OpenCV
        fuente = cv2.FONT_HERSHEY_SIMPLEX
        escala = 1.5
        grosor = 3
        color_texto = (0, 150, 0) # Color Verde oscuro en formato BGR (Blue, Green, Red)

        # Recorrer la cuadrícula celda por celda
        for i in range(9):
            for j in range(9):
                # Si la celda original estaba vacía (0), significa que el algoritmo
                # calculó su valor y debemos dibujarlo
                if matriz_inicial[i][j] == 0:
                    numero = str(matriz_resuelta[i][j])
                    
                    # Calcular el tamaño de la caja de texto del número para poder centrarlo
                    (w, h), _ = cv2.getTextSize(numero, fuente, escala, grosor)
                    
                    # Calcular las coordenadas exactas (x, y) de la esquina inferior izquierda del texto
                    # para que quede perfectamente alineado en el centro de la celda fotográfica
                    x = (j * paso_x) + (paso_x - w) // 2
                    y = (i * paso_y) + (paso_y + h) // 2
                    
                    # Dibujar el texto sobre la imagen (cv2.LINE_AA mejora el renderizado de los bordes)
                    cv2.putText(img, numero, (x, y), fuente, escala, color_texto, grosor, cv2.LINE_AA)

        # Determinar el nombre de archivo final y guardar en disco
        ruta_solucion = ruta_recorte.replace("_recortado.png", "_solucion.png")
        cv2.imwrite(ruta_solucion, img)
        
        # Registrar la ruta de la evidencia final en el estado global
        estado["metadatos"]["imagen_solucion"] = ruta_solucion
        logger.info(f"Imagen con la solución generada en: {ruta_solucion}")
        return True

    except Exception as e:
        logger.error(f"Error al dibujar la solución: {str(e)}")
        return False