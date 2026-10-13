# Automatizador y Solucionador de Sudokus (Vozpópuli / AmuseLabs)

Este proyecto tiene como objetivo automatizar la extracción, reconocimiento y resolución de tableros de Sudoku publicados en plataformas web como AmuseLabs (utilizadas habitualmente en medios como Vozpópuli). 

El flujo completo abarca desde 
* la captura visual del juego en el navegador, 
* el reconocimiento mediante visión artificial (OCR)
* la obtención de su solución lógica 
* su visualización en una interfaz gráfica.
* y la inyección automatizada de la solución en la página web original.

---

## 📂 Estructura del Proyecto

La arquitectura del proyecto está diseñada de forma modular para separar claramente las responsabilidades. 

Se apoya en un gestor de estado centralizado (JSON) que acompaña la ejecución de principio a fin:

```text
.
├── config
│   └── config.json            # Parámetros globales, URLs, tiempos y configuración del navegador
├── imagenes                   # Carpeta de salida para capturas fotográficas y resultados visuales
├── logs                       # Almacenamiento de registros de ejecución (logs) con rotación
├── gui.py                     # Interfaz gráfica (Tkinter) con buscador y visualización en tiempo real
├── main.py                    # Script de consola (CLI) que orquesta secuencialmente el pipeline
├── module
│   ├── buscador.py            # Extrae las URLs reales de los sudokus diarios desde Vozpópuli
│   ├── captura.py             # Automatiza Playwright para navegar y capturar el canvas web
│   ├── deteccion.py           # Usa OpenCV para aislar, aplanar y recortar la cuadrícula
│   ├── dibujado.py            # Superpone los números resueltos sobre la imagen fotográfica original
│   ├── inyeccion.py           # Inyecta la solución simulando clics y pulsaciones en el DOM web
│   ├── reconocimiento.py      # Divide la imagen y usa Tesseract OCR para digitalizar los números
│   ├── solucionador.py        # Motor matemático (Backtracking) que halla la solución exacta
│   └── validacion.py          # Revisa que la matriz extraída no rompa las reglas lógicas del Sudoku
├── requeriments.txt           # Lista de dependencias de Python (Playwright, OpenCV, PyTesseract, etc.)
└── utils
    ├── logger.py              # Sistema centralizado de registro de eventos configurado por config.json
    └── state_manager.py       # Crea y gestiona el JSON de estado que viaja entre todos los módulos
```

---

## 🧩 Descripción de los Módulos

### 1. `config/config.json`

* **Propósito:** Almacenar parámetros globales del sistema, tales como 
    * la URL objetivo por defecto
    * configuración de ejecución del navegador (modo *headless*)
    * tiempos de espera 
    * rutas de directorios.

### 2. Archivos de Utilidades (`utils/`)

* **`logger.py`:** Provee un sistema unificado y estructurado de registro de eventos (`logging`) para facilitar la depuración y trazabilidad en cada etapa del flujo del programa. En el fichero `config.json` se define el rotado del mismo.

* **`state_manager.py`:** Gestiona el "estado" de la aplicación. Genera y guarda un archivo JSON (`estado_sudoku_YYYYMMDD_HHMMSS.json`) que almacena las rutas de las imágenes, los tiempos de ejecución de cada fase, y las matrices del tablero (inicial y resuelta).

Recuerda que el programa fenera varios ficheros:

* un json resumen por cada ejecución
* varios ficheros `png` con lo que genera cada parte del proceso como evidencia.
    * una foto del tablero inicial completo de lo que se extraer del que propone el jeugo
    * una foto editada con solo el tablero inicial
    * una foto con el sudoku resuelto

### 3. Procesamiento y Lógica (`module/`)

* **`captura.py`:** Automatiza la interacción web mediante **Playwright**. Navega a la URL del sudoku (configurable dinámicamente), espera a que el *canvas* se renderice y realiza una captura de pantalla limpia de la cuadrícula. Se ha usado un navegador chromiun oculto que el usuario no verá en ningún momento, pero que consume recursos.

* **`deteccion.py`:** Procesa la captura utilizando **OpenCV**. Aplica umbralización, localiza el contorno cuadrado más grande (el tablero) y realiza una transformación de perspectiva para recortar y aplanar la imagen, preparándola para la lectura.

* **`reconocimiento.py`:** Divide el tablero recortado en 81 celdas y utiliza **Tesseract OCR** para leer los dígitos impresos. Transforma la información visual en una matriz numérica. Es necesario saber instalar el programa en el equipo que trata de resolver el problema.

* **`validacion.py`:** Verifica que la matriz extraída de 9x9 cumple estrictamente con las reglas lógicas del Sudoku antes de enviarla al motor matemático.

* **`solucionador.py`:** Implementa un algoritmo de **Backtracking** (vuelta atrás) para calcular las celdas vacías y encontrar la solución exacta del puzle de manera ultra-rápida.

* **`dibujado.py`:** Toma la matriz resuelta y la superpone sobre la imagen del tablero original utilizando OpenCV, generando una nueva imagen con los números resueltos en otro color (ej. verde).

* **`inyeccion.py`:** Interactúa directamente con el Document Object Model (DOM) de la página web. Localiza los elementos HTML de las celdas, hace clic en los huecos vacíos y envía pulsaciones de teclado para completar el juego online como si fuera un humano.


* **`buscador.py`:** Trata de descubrir las URL que proponen los juegos para encontrar el tablero inicial. Nos basamos en un `json` dentro del código con las características que ha definido el periódico digital:
    * Nivel principiante
    * Nivel medio
    * Nivel complejo
    ```json
        urls_base = {
            "Fácil": "https://www.vozpopuli.com/juegos/sudoku-facil",
            "Medio": "https://www.vozpopuli.com/juegos/sudoku-medio",
            "Difícil": "https://www.vozpopuli.com/juegos/sudoku-dificil"
        }
    ```

### 4. Orquestadores

* **`main.py`:** Script para la ejecución en consola (CLI). Ejecuta el pipeline completo de manera secuencial y genera los archivos de log, estado JSON e imágenes en sus respectivas carpetas. Aquí es necesario saber la URL de alguna manera y no hay interacción con `buscador.py`.

* **`gui.py`:** Interfaz gráfica interactiva desarrollada con Tkinter. Permite introducir URLs de forma dinámica, visualiza un log reducido en tiempo real de los tiempos y fases del pipeline, y muestra la imagen del sudoku resuelto directamente en pantalla. Incluye un botón para buscar las propuestas del diario digital y otro para aplicar e inyectar la solución en el navegador.

---

## 🚀 Requisitos e Instalación

1. **Instalación de utilidades del sistema:**
   Necesitarás instalar el motor de reconocimiento de texto en tu sistema operativo:
   * Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   * Fedora/CentOS: `sudo dnf install tesseract`
   * Arch Linux: `sudo pacman -S tesseract tesseract-data-spa`
   * macOS: `brew install tesseract`
   * Windows: `winget install -e --id UB-Mannheim.TesseractOCR`
        * Nota para Windows: s posible que el usuario necesite añadir la ruta de instalación (habitualmente `C:\Program Files\Tesseract-OCR`) a las variables de entorno `PATH` de su sistema, o definirla explícitamente en el código de Python (`pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`). También existe un repositorio oficial de este programa: Buscar `UB-Mannheim`


2. **Configuración del entorno virtual y dependencias de Python:**
    Para aislar las dependencias del proyecto de tu sistema global, es recomendable utilizar un entorno virtual. Abre una terminal en la raíz del proyecto y sigue estos pasos:

    * Crear el entorno virtual:
    ```bash
    python -m venv .venv
    ```    
    * Activar el entorno virtual (Linux/macOS):
    ```bash
    source .venv/bin/activate
    ```    
    * Activar el entorno virtual (Windows):
    ```bash
    .venv\Scripts\activate
    ```    
    * Instalar las dependencias del proyecto:
    ```bash
    pip install -r requeriments.txt
    ```    

4. **Instalación de navegadores de Playwright:**
    Una vez activado el entorno e instaladas las dependencias, descarga los navegadores necesarios ejecutando:
    ```bash
    playwright install chromium
    ```    

### Espacio de disco usado en un equipo

Una vez creado el entorno virtual, el peso de ese entorno virtual será aproximadamente de 436 MB

```bash
du -sh .venv
```
```text
436M	.venv/
```

Ademá el navegador Chromium no se guarda dentro del proyecto ni del entorno local, sin una su caché dentro del equipo que se ejecuta

```bash
du -sh ~/.cache/ms-playwright/
```
```text
658M	/home/jra/.cache/ms-playwright/
```
Al menos se generarán estar carpetas:

* chromium-1243
* chromium_headless_shell-1243
* ffmpeg-1011

Total **1 GB de espacio en disco**  para resolver el probelma con las herramientas necesarias.

Como es necesario un programa adicional Tesseract OCR, éste tieene un tamaño irrelevante con respecto al entorno virtual:

```bash
pacman -Qi tesseract
```

```text
Nombre                    : tesseract
Versión                   : 5.5.3-1
Descripción               : An OCR program
Arquitectura              : x86_64
URL                       : https://github.com/tesseract-ocr/tesseract
...
Tamaño de la instalación  : 4,66 MiB
Encargado                 : Caleb Maclennan <alerque@archlinux.org>
Fecha de creación         : vie 24 jul 2026 20:47:31
Fecha de instalación      : dom 11 oct 2026 22:24:08
```

---

## ⚙️ Configuración Inicial

Antes de ejecutar el proyecto, asegúrate de crear el archivo `config/config.json` con la siguiente estructura. Esto define la URL objetivo inicial y el comportamiento del navegador:

```json
{
    "app": {
        "name": "Sudoku Solver Automation",
        "version": "1.1.0",
        "debug_mode": true
    },
    "logger": {
        "log_dir": "logs",
        "log_file": "sudoku_app.log",
        "log_level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    },
    "browser": {
        "url": "[https://puzzleme.amuselabs.com/pmm/sudoku?id=sudoku-dificil&set=0203&embed=1](https://puzzleme.amuselabs.com/pmm/sudoku?id=sudoku-dificil&set=0203&embed=1)",
        "headless": true,
        "timeout_seconds": 15
    },
    "paths": {
        "images_dir": "imagenes"
    }
}
```

---

## 🎮 Uso

**Para ejecutar la interfaz gráfica (Recomendado):**
```bash
python gui.py
```
Desde la interfaz, puedes pegar la URL de cualquier Sudoku de AmuseLabs, iniciar la resolución y ver los resultados en pantalla.

**Para ejecutar por consola:**
```bash
python main.py
```
Revisará la URL configurada en `config.json` y depositará los resultados y evidencias en las carpetas `imagenes/` y la raíz del proyecto.

## Telemetría y rendimiento

El log del programa `sudoku_app.log` detalla cada parte del flujo del programa y el JSON resumen detalla los tiempos exactos que tarda cada fase. Una vez aplicada la inyección, el JSON reflejará un desglose similar a este:

```json
    "tiempos": {
        "fase_captura_segundos": 6.03,
        "fase_deteccion_segundos": 0.06,
        "fase_ocr_segundos": 9.69,
        "fase_resolucion_segundos": 0.0038,
        "fase_inyeccion_segundos": 13.19,
        "tiempo_total_segundos": 29.05
    }
```

Repasando estos ficheros el programa podrá hacer estadísticas de la eficiencia general. Obsérvese que el tiempo de resolución matemática pura de un tablero bien formado (Backtracking) es prácticamente instantáneo (0.0038s) en comparación con el trabajo de Visión Artificial, OCR o la inyección DOM que requiere pausas para imitar a un humano de manera segura.

No se ha querido resolver de momento en el sitio original el tablero.