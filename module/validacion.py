"""
Archivo: module/validacion.py
Ruta relativa: ./module/validacion.py

Descripción:
    Módulo encargado de controlar la calidad de los datos extraídos por el OCR.
    
    Antes de enviar la matriz al motor de resolución matemática, este módulo 
    verifica dos cosas fundamentales:
      1. Que la estructura de datos sea una cuadrícula perfecta de 9x9.
      2. Que los números detectados inicialmente no violen las reglas básicas 
         del Sudoku (no haya números repetidos en la misma fila, columna o 
         subcuadrícula de 3x3).
         
    Esto previene que el solucionador entre en bucles infinitos intentando 
    resolver un tablero mal leído por la visión artificial.
"""

from utils.logger import logger

def es_movimiento_valido(matriz, fila, col, num):
    """
    Verifica si un número puede colocarse en una posición dada según las 
    reglas clásicas del Sudoku.
    
    Args:
        matriz (list of lists): La cuadrícula actual del Sudoku de 9x9.
        fila (int): Índice de la fila (0-8) donde se quiere evaluar el número.
        col (int): Índice de la columna (0-8) donde se quiere evaluar el número.
        num (int): El dígito (1-9) a evaluar.
        
    Returns:
        bool: True si el movimiento es legal, False si choca con otro número.
    """
    # 1. Revisar colisiones en la misma fila
    if num in matriz[fila]:
        return False
        
    # 2. Revisar colisiones en la misma columna
    if num in [matriz[i][col] for i in range(9)]:
        return False
        
    # 3. Revisar colisiones en la subcuadrícula de 3x3 correspondiente
    # Calculamos la esquina superior izquierda del cuadrante 3x3 al que pertenece la celda
    inicio_fila, inicio_col = 3 * (fila // 3), 3 * (col // 3)
    for i in range(inicio_fila, inicio_fila + 3):
        for j in range(inicio_col, inicio_col + 3):
            if matriz[i][j] == num:
                return False
                
    return True

def validar_matriz(estado):
    """
    Comprueba que la matriz extraída tiene el formato correcto (9x9) y que 
    los números iniciales no contienen errores evidentes que hagan el puzle irresoluble.
    
    Si la validación es exitosa, actualiza la bandera 'es_valido' en el estado global.
    
    Args:
        estado (dict): Diccionario global que contiene el estado del pipeline, 
                       incluyendo la 'matriz_inicial' generada por el OCR.
                       
    Returns:
        bool: True si la matriz supera todas las comprobaciones lógicas, False en caso contrario.
    """
    matriz = estado["datos_sudoku"].get("matriz_inicial", [])
    
    # Verificación estructural: debe ser exactamente de 9x9
    if not matriz or len(matriz) != 9 or any(len(fila) != 9 for fila in matriz):
        logger.error("La matriz no tiene dimensiones 9x9. Posible fallo crítico en el OCR o recorte.")
        return False

    # Verificación lógica: validar que no haya duplicados iniciales que rompan las reglas
    for i in range(9):
        for j in range(9):
            num = matriz[i][j]
            
            # Solo comprobamos las celdas que ya tienen un número detectado
            if num != 0:
                # Quitamos el número temporalmente de la matriz para no evaluarlo contra sí mismo
                matriz[i][j] = 0
                valido = es_movimiento_valido(matriz, i, j, num)
                matriz[i][j] = num # Lo restauramos a su posición original
                
                # Si descubrimos que la posición inicial choca con otra, el tablero es inválido
                if not valido:
                    logger.error(f"Inconsistencia detectada en la posición inicial [{i}][{j}] con el número {num}.")
                    return False
                    
    # Si termina el bucle sin retornar False, el tablero es perfectamente válido
    estado["datos_sudoku"]["es_valido"] = True
    logger.info("La matriz inicial ha superado la validación de reglas del Sudoku.")
    return True