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
	'datos_principales': 7200,  # 2 horas - datos cambian poco
	'graficos': 3600,          # 1 hora - gráficos son costosos
	'estadisticas': 1800,      # 30 minutos - cálculos estadísticos
	'selecciones': 600,        # 10 minutos - selecciones de usuario
	'preparacion_datos': 1800, # 30 minutos - procesamiento de datos
	'jugadores_categoria': 3600 # 1 hora - listas de jugadores
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
# Mapeo: Columna original en Excel → Etiqueta para visualización
METRICAS_ZSCORE_FUERZA = {
	'CUAD DER (N)': 'CUAD Der',
	'CUAD IZQ (N)': 'CUAD Izq',
	'WOLLIN DER': 'ISQ Der',
	'WOLLIN IZQ': 'ISQ Izq',
	'F PICO DER (IMTP) (N)': 'IMTP Der',
	'F PICO IZQ (IMTP) (N)': 'IMTP Izq',
	'F PICO (IMTP) (N)': 'IMTP Total',
	'FP DER (CMJ) (N)': 'CMJ FP Der',
	'FP IZQ (CMJ) (N)': 'CMJ FP Izq',
	'FP (CMJ) (N)': 'CMJ FP Total',
	'FF DER (CMJ) (N)': 'CMJ FF Der',
	'FF IZQ (CMJ) (N)': 'CMJ FF Izq',
	'FF (CMJ) (N)': 'CMJ FF Total'
}

# Configuración simplificada para radar (máximo 5 métricas)
METRICAS_ZSCORE_RADAR_SIMPLE = {
	# Usar métricas totales o promediar bilaterales automáticamente
	'F PICO (IMTP) (N)': 'IMTP',
	'FP (CMJ) (N)': 'CMJ Propulsiva', 
	'FF (CMJ) (N)': 'CMJ Frenado',
	# Para bilaterales, calcular promedio automáticamente
	'CUAD_PROMEDIO': 'CUAD',
	'WOLLIN_PROMEDIO': 'ISQ Wollin'
}

# Configuración de métricas de movilidad para radar
METRICAS_ZSCORE_MOVILIDAD = {
	# Para bilaterales, calcular promedio automáticamente
	'AKE_PROMEDIO': 'AKE',
	'THOMAS_PROMEDIO': 'THOMAS',
	'LUNGE_PROMEDIO': 'LUNGE'
}

# Configuración legacy para compatibilidad (si existe en Excel)
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
