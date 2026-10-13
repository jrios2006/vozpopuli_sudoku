"""
Archivo: utils/logger.py
Ruta relativa: ./utils/logger.py

Descripción:
    Módulo de registro de eventos (Logging).
    Este módulo lee la configuración desde `config/config.json` y establece
    un logger unificado para toda la aplicación.
    
    Incluye un sistema de rotación de logs (RotatingFileHandler) para evitar 
    que el archivo crezca indefinidamente, manteniendo un tamaño máximo y un 
    número determinado de copias de seguridad.

    Exporta una instancia `logger` lista para ser importada en cualquier otro archivo.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import json

def load_config():
    """
    Carga la configuración desde el archivo JSON principal.
    
    Returns:
        dict: Diccionario con la configuración. Retorna un diccionario
              vacío si el archivo no existe.
    """
    config_path = os.path.join("config", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def setup_logger(name="SudokuSolver"):
    """
    Configura y devuelve un logger unificado con rotación de archivos.
    Crea automáticamente la carpeta de logs si no existe en el sistema.
    
    Args:
        name (str): Nombre del logger. Por defecto "SudokuSolver".
        
    Returns:
        logging.Logger: Instancia del logger configurada para consola y archivo (con rotación).
    """
    config = load_config()
    logger_config = config.get("logger", {})
    
    log_dir = logger_config.get("log_dir", "logs")
    log_file_name = logger_config.get("log_file", "sudoku_app.log")
    log_level_str = logger_config.get("log_level", "DEBUG")
    log_format = logger_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Parámetros de rotación (pueden añadirse al config.json; si no, usan estos valores por defecto)
    max_bytes = logger_config.get("max_bytes", 5 * 1024 * 1024) # 5 MB por defecto
    backup_count = logger_config.get("backup_count", 3) # Guardar 3 archivos antiguos por defecto

    # Mapeo de niveles de log
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    level = level_mapping.get(log_level_str.upper(), logging.DEBUG)

    # Crear la carpeta de logs si no existe
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_path = os.path.join(log_dir, log_file_name)

    # Configurar la instancia del logger
    logger_instance = logging.getLogger(name)
    logger_instance.setLevel(level)

    # Evitar duplicidad de handlers si ya fue configurado previamente
    if not logger_instance.handlers:
        # Handler para escribir en archivo con rotación
        file_handler = RotatingFileHandler(
            log_path, 
            maxBytes=max_bytes, 
            backupCount=backup_count, 
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger_instance.addHandler(file_handler)

        # Handler para mostrar en consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(log_format))
        logger_instance.addHandler(console_handler)

    return logger_instance

# Instancia global lista para importar en otros módulos
logger = setup_logger()