"""
Archivo: gui.py
Ruta relativa: ./gui.py

Descripción:
    Interfaz Gráfica de Usuario (GUI) para el Sudoku Solver Automation.
    Integra la funcionalidad de buscar automáticamente los puzles del día 
    desde Vozpópuli, el pipeline completo de resolución visual, y la 
    inyección de la solución directamente en el navegador web.
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
from PIL import Image, ImageTk
import threading
import time
import os

# Módulos del pipeline y utilidades
from utils.state_manager import inicializar_estado, guardar_estado
from utils.logger import load_config # <-- AÑADIDO IMPORT DE CONFIGURACIÓN
from module.captura import capturar_tablero_sudoku
from module.deteccion import procesar_tablero
from module.reconocimiento import extraer_numeros
from module.validacion import validar_matriz
from module.solucionador import resolver_sudoku
from module.dibujado import generar_imagen_solucion
from module.buscador import obtener_urls_del_dia
from module.inyeccion import inyectar_solucion  

class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver Bot")
        self.root.geometry("850x800") 

        self.estado_actual = None 

        # ---------------------------------------------------------
        # Buscador Automático de Puzles
        # ---------------------------------------------------------
        frame_buscador = tk.Frame(root)
        frame_buscador.pack(pady=10, fill=tk.X, padx=20)
        
        self.btn_buscar = tk.Button(frame_buscador, text="🔍 Buscar Sudokus de Hoy", command=self.iniciar_busqueda, font=("Arial", 10, "bold"))
        self.btn_buscar.pack(side=tk.LEFT)
        
        tk.Label(frame_buscador, text="Dificultad:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(20, 5))
        
        self.combo_sudokus = ttk.Combobox(frame_buscador, state="readonly", width=15, font=("Arial", 10))
        self.combo_sudokus.pack(side=tk.LEFT)
        self.combo_sudokus.bind("<<ComboboxSelected>>", self.seleccionar_dificultad)
        
        self.urls_encontradas = {}

        # ---------------------------------------------------------
        # Campo de URL a resolver
        # ---------------------------------------------------------
        frame_url = tk.Frame(root)
        frame_url.pack(pady=5, fill=tk.X, padx=20)
        
        tk.Label(frame_url, text="URL del Sudoku:", font=("Arial", 12)).pack(side=tk.LEFT)
        
        self.entry_url = tk.Entry(frame_url, font=("Arial", 10))
        self.entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # --- AÑADIDO: Leer la URL por defecto desde el config.json ---
        config = load_config()
        url_por_defecto = config.get("browser", {}).get("url", "")
        self.entry_url.insert(0, url_por_defecto)

        # ---------------------------------------------------------
        # Controles y Visualización del Pipeline
        # ---------------------------------------------------------
        self.btn_iniciar = tk.Button(root, text="Iniciar Resolución Automática", command=self.iniciar_pipeline, font=("Arial", 14))
        self.btn_iniciar.pack(pady=10)

        self.btn_aplicar = tk.Button(root, text="▶️ Aplicar Solución en Web", command=self.iniciar_inyeccion, font=("Arial", 14, "bold"), state=tk.DISABLED, bg="#4CAF50", fg="white")
        self.btn_aplicar.pack(pady=5)

        self.log_text = scrolledtext.ScrolledText(root, height=10, width=95, state=tk.DISABLED, bg="#f4f4f4")
        self.log_text.pack(pady=10)

        self.panel_imagen = tk.Label(root)
        self.panel_imagen.pack(pady=10)

    # ---------------------------------------------------------
    # Métodos del Buscador
    # ---------------------------------------------------------
    def iniciar_busqueda(self):
        self.btn_buscar.config(state=tk.DISABLED)
        self.combo_sudokus.set('')
        self.log("Navegando por Vozpópuli para encontrar los sudokus de hoy. Esto puede tardar unos segundos...")
        threading.Thread(target=self.ejecutar_busqueda).start()

    def ejecutar_busqueda(self):
        enlaces = obtener_urls_del_dia()
        self.urls_encontradas = enlaces
        
        if enlaces:
            opciones = list(enlaces.keys())
            self.combo_sudokus['values'] = opciones
            self.combo_sudokus.current(0)
            self.seleccionar_dificultad(None)
            self.log(f"¡Éxito! Se encontraron {len(enlaces)} puzles actualizados.")
        else:
            self.log("No se pudieron extraer los enlaces de los sudokus hoy.")
            
        self.btn_buscar.config(state=tk.NORMAL)

    def seleccionar_dificultad(self, event):
        seleccion = self.combo_sudokus.get()
        if seleccion in self.urls_encontradas:
            url_real = self.urls_encontradas[seleccion]
            self.entry_url.delete(0, tk.END)
            self.entry_url.insert(0, url_real)
            self.log(f"URL de dificultad '{seleccion}' inyectada y lista para resolver.")

    # ---------------------------------------------------------
    # Métodos de Utilidad UI
    # ---------------------------------------------------------
    def log(self, mensaje):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, mensaje + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def mostrar_imagen(self, ruta_imagen):
        if os.path.exists(ruta_imagen):
            img = Image.open(ruta_imagen)
            img.thumbnail((400, 400))
            img_tk = ImageTk.PhotoImage(img)
            self.panel_imagen.config(image=img_tk)
            self.panel_imagen.image = img_tk

    # ---------------------------------------------------------
    # Métodos de Resolución (Pipeline Principal)
    # ---------------------------------------------------------
    def iniciar_pipeline(self):
        url_actual = self.entry_url.get().strip()
        if not url_actual:
            self.log("Por favor, introduce una URL válida.")
            return
            
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_buscar.config(state=tk.DISABLED)
        self.btn_aplicar.config(state=tk.DISABLED)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.panel_imagen.config(image='')
        self.estado_actual = None 
        
        hilo = threading.Thread(target=self.ejecutar_proceso, args=(url_actual,))
        hilo.start()

    def ejecutar_proceso(self, url):
        tiempo_inicio_global = time.time()
        estado = inicializar_estado()
        
        self.log(f"Iniciando flujo para: {url}")
        
        self.log("Fase 1: Extrayendo imagen del navegador...")
        if not capturar_tablero_sudoku(estado, url_dinamica=url):
            self.log("ERROR: Fallo en la captura.")
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_buscar.config(state=tk.NORMAL)
            return

        self.log("Fase 2: Detectando y recortando cuadrícula...")
        if not procesar_tablero(estado):
            self.log("ERROR: Fallo en detección.")
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_buscar.config(state=tk.NORMAL)
            return

        self.log("Fase 3: Ejecutando OCR (Reconocimiento de dígitos)...")
        if not extraer_numeros(estado):
            self.log("ERROR: Fallo en OCR.")
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_buscar.config(state=tk.NORMAL)
            return

        self.log("Fase 4: Validando reglas lógicas...")
        if not validar_matriz(estado):
            self.log("ERROR: Matriz inválida.")
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_buscar.config(state=tk.NORMAL)
            return

        self.log("Fase 5: Resolviendo por Backtracking...")
        if not resolver_sudoku(estado):
            self.log("ERROR: No se encontró solución.")
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_buscar.config(state=tk.NORMAL)
            return

        self.log("Fase 6: Dibujando solución en la imagen...")
        generar_imagen_solucion(estado)
        
        tiempo_fin_global = time.time()
        estado["tiempos"]["tiempo_total_segundos"] = round(tiempo_fin_global - tiempo_inicio_global, 2)
        
        nombre_base = os.path.basename(estado["metadatos"]["imagen_path"])
        nombre_json = "estado_" + nombre_base.replace(".png", ".json")
        guardar_estado(estado, nombre_json)

        self.mostrar_imagen(estado["metadatos"]["imagen_solucion"])
        self.log("\n--- Proceso completado con éxito ---")
        self.log(f"⏱️ TIEMPO TOTAL: {estado['tiempos']['tiempo_total_segundos']} s")
        
        self.estado_actual = estado
        self.btn_aplicar.config(state=tk.NORMAL)
        
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_buscar.config(state=tk.NORMAL)

    # ---------------------------------------------------------
    # Métodos de Inyección
    # ---------------------------------------------------------
    def iniciar_inyeccion(self):
        """Lanza la inyección en un hilo separado al hacer clic en 'Aplicar Solución'."""
        self.btn_aplicar.config(state=tk.DISABLED)
        self.log("\nFase 7: Abriendo navegador para inyectar solución...")
        threading.Thread(target=self.ejecutar_inyeccion).start()

    def ejecutar_inyeccion(self):
        """Ejecuta la automatización web basada en el estado actual."""
        if self.estado_actual:
            if inyectar_solucion(self.estado_actual):
                self.log(f"¡El Sudoku ha sido completado exitosamente en la web! (Tiempo de inyección: {self.estado_actual['tiempos']['fase_inyeccion_segundos']}s)")
                
                nombre_base = os.path.basename(self.estado_actual["metadatos"]["imagen_path"])
                nombre_json = "estado_" + nombre_base.replace(".png", ".json")
                guardar_estado(self.estado_actual, nombre_json)
                self.log(f"Archivo JSON actualizado con los tiempos de inyección.")
                
            else:
                self.log("ERROR: Ocurrió un problema al intentar escribir la solución.")
        
        self.btn_aplicar.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()