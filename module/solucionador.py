"""
Archivo: module/solucionador.py
Ruta relativa: ./module/solucionador.py

Descripción:
    Módulo encargado de la resolución matemática del Sudoku.
    
    Implementa un algoritmo de búsqueda en profundidad conocido como 
    'Backtracking' (Vuelta atrás). Este método es extremadamente eficiente para 
    tableros de Sudoku, ya que prueba combinaciones secuencialmente y, si detecta 
    que un camino no tiene salida (no cumple las reglas), retrocede al paso anterior 
    para intentar con el siguiente número.
    
    Una vez resuelto, este módulo guarda la matriz final en el estado global.
"""

import time
import copy
from utils.logger import logger
from module.validacion import es_movimiento_valido

def resolver_backtracking(matriz):
    """
    Función recursiva central que aplica el algoritmo de Backtracking para 
    encontrar la solución al Sudoku.
    
    El algoritmo funciona de la siguiente manera:
      1. Recorre la matriz de izquierda a derecha y de arriba a abajo.
      2. Al encontrar una celda vacía (valor 0), intenta colocar los números del 1 al 9.
      3. Si el número es válido (según `es_movimiento_valido`), lo coloca y se llama 
         a sí misma (recursividad) para intentar resolver el resto del tablero.
      4. Si en algún punto del futuro no se puede colocar ningún número, la función 
         devuelve False, lo que hace que se borre el número actual (se vuelve a 0) 
         y se pruebe con el siguiente. Esto es el "backtrack" (vuelta atrás).
      5. Si se logran rellenar todas las celdas, devuelve True.
    
    Args:
        matriz (list of lists): Cuadrícula de 9x9 que se modificará in-place.
        
    Returns:
        bool: True si se encontró una solución completa, False si el camino 
              actual no lleva a ninguna solución válida.
    """
    for i in range(9):
        for j in range(9):
            # Buscar una celda que esté vacía
            if matriz[i][j] == 0:
                # Intentar colocar un número del 1 al 9
                for num in range(1, 10):
                    if es_movimiento_valido(matriz, i, j, num):
                        matriz[i][j] = num # Asignación temporal
                        
                        # Llamada recursiva: intentar resolver el resto del tablero
                        if resolver_backtracking(matriz):
                            return True
                            
                        # Si llegamos aquí, significa que la elección anterior no 
                        # llevaba a la solución final. Deshacemos el movimiento (Backtrack).
                        matriz[i][j] = 0 
                
                # Si hemos probado del 1 al 9 en esta celda y ninguno sirve, 
                # esta rama de la resolución está muerta.
                return False
                
    # Si se han recorrido todas las celdas y no queda ningún 0, el sudoku está resuelto.
    return True

def resolver_sudoku(estado):
    """
    Ejecuta el algoritmo de resolución sobre una copia de la matriz inicial
    y actualiza el estado global con los resultados y los tiempos de procesamiento.
    
    Se asegura de no intentar resolver tableros que previamente fallaron la 
    validación de reglas lógicas.
    
    Args:
        estado (dict): Diccionario global que contiene la 'matriz_inicial' validada.
        
    Returns:
        bool: True si el Sudoku se resolvió correctamente, False en caso contrario.
    """
    tiempo_inicio = time.time()
    
    # Comprobación de seguridad: solo resolver si la validación previa fue exitosa
    if not estado["datos_sudoku"].get("es_valido", False):
        logger.error("No se puede resolver un sudoku que no ha pasado la validación.")
        return False

    matriz_original = estado["datos_sudoku"]["matriz_inicial"]
    
    # Realizamos una copia profunda (deepcopy) para no sobrescribir la matriz inicial.
    # Así en el JSON final podremos ver el "Antes" y el "Después".
    matriz_trabajo = copy.deepcopy(matriz_original)
    
    logger.info("Iniciando motor de resolución por Backtracking...")
    
    # Ejecutamos el algoritmo sobre la copia de trabajo
    if resolver_backtracking(matriz_trabajo):
        # Guardamos los resultados
        estado["datos_sudoku"]["matriz_resuelta"] = matriz_trabajo
        estado["datos_sudoku"]["resuelto"] = True
        
        tiempo_fin = time.time()
        estado["tiempos"]["fase_resolucion_segundos"] = round(tiempo_fin - tiempo_inicio, 4)
        
        logger.info(f"¡Sudoku resuelto en {estado['tiempos']['fase_resolucion_segundos']}s!")
        return True
    else:
        logger.error("El algoritmo determinó que este Sudoku no tiene solución.")
        return False