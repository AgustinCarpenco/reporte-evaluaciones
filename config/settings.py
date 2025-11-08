"""
Configuración general de la aplicación
"""

# ========= CONFIGURACIÓN DE RUTAS ==========
import os

# Rutas relativas para compatibilidad local y Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "EVALUACIONES.xlsx")
ESCUDO_PATH = os.path.join(BASE_DIR, "data", "escudo.png")

# ========= CONFIGURACIÓN DE CACHE ==========
CACHE_TTL = {
	'datos_principales': 3600,  # 1 hora
	'graficos': 1800,          # 30 minutos
	'estadisticas': 900,       # 15 minutos
	'selecciones': 300,        # 5 minutos
	'preparacion_datos': 600,  # 10 minutos
	'jugadores_categoria': 1800 # 30 minutos
}

# ========= MAPEO DE COLUMNAS NUEVA EVALUACIÓN ==========
MAPEO_COLUMNAS_NUEVA_EVALUACION = {
	# Mapeo de columnas: Formato Anterior → Formato Nuevo
	"CUAD 70° Der": "CUAD DER (N)",
	"CUAD 70° Izq": "CUAD IZQ (N)",
	"ISQ Wollin Der": "WOLLIN DER",
	"ISQ Wollin Izq": "WOLLIN IZQ",
	"IMTP F. Der (N)": "F PICO DER (IMTP) (N)",
	"IMTP F. Izq (N)": "F PICO IZQ (IMTP) (N)",
	"CMJ F. Der (N)": "FP DER (CMJ) (N)",
	"CMJ F. Izq (N)": "FP IZQ (CMJ) (N)",
	"CMJ F. Der (N).1": "FF DER (CMJ) (N)",
	"CMJ F. Izq (N).1": "FF IZQ (CMJ) (N)",
	# Mapeo de columnas de identificación
	"Deportista": "JUGADOR"
}

# ========= CONFIGURACIÓN DE MÉTRICAS ==========
METRICAS_POR_SECCION = {
	"Fuerza": {
		"CUAD DER (N)": "CUAD IZQ (N)",
		"WOLLIN DER": "WOLLIN IZQ", 
		"F PICO DER (IMTP) (N)": "F PICO IZQ (IMTP) (N)",
		"FP DER (CMJ) (N)": "FP IZQ (CMJ) (N)"
	},
	"Movilidad": {
		"AKE DER": "AKE IZQ",
		"THOMAS DER": "THOMAS IZQ",
		"LUNGE DER": "LUNGE IZQ"
	},
	"Funcionalidad": {
		"TRIPLE SALTO DER": "TRIPLE SALTO IZQ"
	}
}

# ========= CONFIGURACIÓN DE COLORES ==========
COLORES = {
	'rojo_colon': 'rgba(220, 38, 38, 0.85)',
	'negro_colon': 'rgba(31, 41, 55, 0.85)',
	'fondo_oscuro': 'rgba(17, 24, 39, 1)',
	'azul_zscore': 'rgba(59, 130, 246, 0.8)',
	'verde_optimo': 'rgba(50, 205, 50, 0.9)',
	'naranja_alerta': 'rgba(255, 165, 0, 0.9)',
	'rojo_riesgo': 'rgba(255, 69, 0, 0.9)'
}

# ========= CONFIGURACIÓN DE Z-SCORES ==========
Z_SCORE_METRICAS = {
	'Z SCORE CUAD Der': 'CUAD Der',
	'Z SCORE CUAD Izq': 'CUAD Izq',
	'Z SCORE ISQ Der': 'ISQ Der',
	'Z SCORE ISQ Izq': 'ISQ Izq',
	'Z SCORE F PICO': 'F PICO',
	'Z SCORE F PROP': 'F PROP',
	'Z SCORE F FREN': 'F FREN'
}

# ========= CONFIGURACIÓN DE PLOTLY ==========
PLOTLY_CONFIG = {
	'displayModeBar': True,
	'displaylogo': False,
	'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
	'toImageButtonOptions': {
		'format': 'png',
		'height': 620,
		'width': 1000,
		'scale': 2
	}
}
