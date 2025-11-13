"""
Utilidades para manejo de datos
"""

import pandas as pd
import streamlit as st
import json
import hashlib
import os
from config.settings import CACHE_TTL, DATA_PATH, MAPEO_COLUMNAS_NUEVA_EVALUACION

@st.cache_data(ttl=CACHE_TTL['datos_principales'], show_spinner="Cargando datos de evaluaciones...")
def cargar_evaluaciones(path_excel):
	"""Carga y procesa datos de evaluaciones con cache optimizado - Nueva versión EVALUACIONES.xlsx"""
	# Validar que el archivo existe
	if not os.path.exists(path_excel):
		st.error(f"❌ No se encontró el archivo Excel en: {path_excel}")
		st.info("💡 Asegúrate de que el archivo 'EVALUACIONES.xlsx' esté en la carpeta 'data/'")
		st.stop()
	
	try:
		# Cargar desde la nueva hoja EVALUACION 2910 con optimizaciones
		df_evaluacion = pd.read_excel(
			path_excel, 
			sheet_name="EVALUACION 2910",
			engine='openpyxl',  # Motor más rápido para archivos .xlsx
			na_values=['', ' ', 'N/A', 'n/a', 'NULL', 'null']  # Valores nulos explícitos
		)
		
		# Optimizar tipos de datos para reducir memoria
		for col in df_evaluacion.columns:
			if df_evaluacion[col].dtype == 'object':
				# Intentar convertir a numérico si es posible
				try:
					numeric_col = pd.to_numeric(df_evaluacion[col])
					df_evaluacion[col] = numeric_col
				except (ValueError, TypeError):
					# Si no es convertible a numérico, optimizar strings como categorías si tienen pocos valores únicos
					unique_ratio = len(df_evaluacion[col].unique()) / len(df_evaluacion[col])
					if unique_ratio < 0.5:  # Si menos del 50% son valores únicos
						df_evaluacion[col] = df_evaluacion[col].astype('category')
		
	except Exception as e:
		st.error(f"❌ Error al leer el archivo Excel: {str(e)}")
		st.info("💡 Verifica que la hoja 'EVALUACION 2910' exista en el archivo")
		st.stop()

	# Mapear columna de jugadores para compatibilidad
	if "JUGADOR" in df_evaluacion.columns:
		df_evaluacion["Deportista"] = df_evaluacion["JUGADOR"]
	
	# Por ahora, asignar todos a una categoría (se puede expandir después)
	# TODO: Implementar lógica de categorías si está disponible en el Excel
	df_evaluacion["categoria"] = "Evaluacion_2910"
	
	return df_evaluacion

def cargar_datos_optimizado(path_excel=None):
	"""Carga datos con optimización de session state"""
	if path_excel is None:
		path_excel = DATA_PATH
		
	if 'df_cache' not in st.session_state or st.session_state.df_cache is None:
		st.session_state.df_cache = cargar_evaluaciones(path_excel)
	return st.session_state.df_cache

@st.cache_data(ttl=CACHE_TTL['jugadores_categoria'])
def obtener_jugadores_categoria(df, categoria_sel):
	"""Obtiene jugadores filtrados por categoría"""
	# Usar la columna correcta según el mapeo
	columna_jugador = "Deportista" if "Deportista" in df.columns else "JUGADOR"
	return df[df["categoria"] == categoria_sel][columna_jugador].dropna().unique()

@st.cache_data(ttl=CACHE_TTL['preparacion_datos'])
def procesar_datos_categoria(df, categoria):
	"""Procesa y filtra datos por categoría con cache"""
	df_categoria = df[df["categoria"] == categoria].copy()
	
	# FILTRAR filas de resumen estadístico
	valores_a_excluir = ['MEDIA', 'SD', 'TOTAL EN RIESGO ALTO', 'RIESGO RELATIVO', 
						'TOTAL EN RIESGO MODERADO', 'TOTAL EN BAJO RIESGO', 
						'Apellido y Nombre', 'ALTO RIESGO', 'MODERADO RIESGO', 'BAJO RIESGO']
	
	df_categoria = df_categoria[
		(~df_categoria['Deportista'].isin(valores_a_excluir)) & 
		(df_categoria['Deportista'].notna()) &
		(~df_categoria['Deportista'].str.contains('RIESGO|MEDIA|TOTAL|SD', case=False, na=False))
	].copy()
	
	return df_categoria

@st.cache_data(ttl=CACHE_TTL['estadisticas'])
def calcular_estadisticas_categoria(df_categoria, columnas_tabla):
	"""Calcula medias y desviaciones estándar con cache"""
	# Forzar a número para evitar errores silenciosos
	for col in list(columnas_tabla.keys()) + list(columnas_tabla.values()):
		if col in df_categoria.columns:
			df_categoria[col] = pd.to_numeric(df_categoria[col], errors="coerce")

	# Calcular medias del grupo
	media_dict = {}
	for col_der, col_izq in columnas_tabla.items():
		if col_der in df_categoria.columns:
			media_val = df_categoria[col_der].mean(skipna=True)
			media_dict[col_der] = round(media_val, 1) if pd.notna(media_val) else 0.0
		else:
			media_dict[col_der] = 0.0
			
		if col_izq in df_categoria.columns:
			media_val = df_categoria[col_izq].mean(skipna=True)
			media_dict[col_izq] = round(media_val, 1) if pd.notna(media_val) else 0.0
		else:
			media_dict[col_izq] = 0.0

	# Calcular desviaciones estándar del grupo
	std_dict = {}
	n_jugadores = len(df_categoria)
	
	for col_der, col_izq in columnas_tabla.items():
		if col_der in df_categoria.columns:
			if n_jugadores > 1:
				std_val = df_categoria[col_der].std(skipna=True)
				std_dict[col_der] = round(std_val, 1) if pd.notna(std_val) else 0.0
			else:
				std_dict[col_der] = 0.0  # Solo un jugador, no hay desviación
		else:
			std_dict[col_der] = 0.0
			
		if col_izq in df_categoria.columns:
			if n_jugadores > 1:
				std_val = df_categoria[col_izq].std(skipna=True)
				std_dict[col_izq] = round(std_val, 1) if pd.notna(std_val) else 0.0
			else:
				std_dict[col_izq] = 0.0  # Solo un jugador, no hay desviación
		else:
			std_dict[col_izq] = 0.0
	
	return media_dict, std_dict

@st.cache_data(ttl=CACHE_TTL['preparacion_datos'])
def preparar_datos_jugador(datos_jugador, columnas_tabla):
	"""Prepara datos del jugador para visualización con cache"""
	jugador_dict = {}
	for col_der, col_izq in columnas_tabla.items():
		jugador_dict[col_der] = round(datos_jugador.get(col_der, 0), 1)
		jugador_dict[col_izq] = round(datos_jugador.get(col_izq, 0), 1)
	return jugador_dict

@st.cache_data(ttl=CACHE_TTL['estadisticas'])
def calcular_estadisticas_completas_categoria(df_categoria, columnas_tabla, columnas_totales):
	"""
	Calcula TODAS las estadísticas de la categoría UNA SOLA VEZ (fijas)
	Incluye métricas bilaterales y totales
	"""
	estadisticas = {
		'media': {},
		'std': {},
		'n_jugadores': len(df_categoria)
	}
	
	# Forzar a número para evitar errores silenciosos
	for col in list(columnas_tabla.keys()) + list(columnas_tabla.values()) + columnas_totales:
		if col in df_categoria.columns:
			df_categoria[col] = pd.to_numeric(df_categoria[col], errors="coerce")

	# Calcular estadísticas para métricas bilaterales
	for col_der, col_izq in columnas_tabla.items():
		# Derecha
		if col_der in df_categoria.columns:
			media_val = df_categoria[col_der].mean(skipna=True)
			estadisticas['media'][col_der] = round(media_val, 1) if pd.notna(media_val) else 0.0
			
			if estadisticas['n_jugadores'] > 1:
				std_val = df_categoria[col_der].std(skipna=True)
				estadisticas['std'][col_der] = round(std_val, 1) if pd.notna(std_val) else 0.0
			else:
				estadisticas['std'][col_der] = 0.0
		else:
			estadisticas['media'][col_der] = 0.0
			estadisticas['std'][col_der] = 0.0
			
		# Izquierda
		if col_izq in df_categoria.columns:
			media_val = df_categoria[col_izq].mean(skipna=True)
			estadisticas['media'][col_izq] = round(media_val, 1) if pd.notna(media_val) else 0.0
			
			if estadisticas['n_jugadores'] > 1:
				std_val = df_categoria[col_izq].std(skipna=True)
				estadisticas['std'][col_izq] = round(std_val, 1) if pd.notna(std_val) else 0.0
			else:
				estadisticas['std'][col_izq] = 0.0
		else:
			estadisticas['media'][col_izq] = 0.0
			estadisticas['std'][col_izq] = 0.0

	# Calcular estadísticas para métricas totales
	for col_total in columnas_totales:
		if col_total in df_categoria.columns:
			valores_totales = pd.to_numeric(df_categoria[col_total], errors="coerce").dropna()
			if len(valores_totales) > 0:
				estadisticas['media'][col_total] = round(valores_totales.mean(), 1)
				if len(valores_totales) > 1:
					estadisticas['std'][col_total] = round(valores_totales.std(), 1)
				else:
					estadisticas['std'][col_total] = 0.0
			else:
				estadisticas['media'][col_total] = 0.0
				estadisticas['std'][col_total] = 0.0
		else:
			estadisticas['media'][col_total] = 0.0
			estadisticas['std'][col_total] = 0.0
	
	return estadisticas

@st.cache_data(ttl=CACHE_TTL['preparacion_datos'])
def preparar_datos_jugador_completo(datos_jugador, columnas_tabla, columnas_totales):
	"""
	Prepara SOLO los datos del jugador seleccionado (dinámico)
	Incluye métricas bilaterales y totales
	"""
	jugador_dict = {}
	
	# Procesar métricas bilaterales
	for col_der, col_izq in columnas_tabla.items():
		# Derecha
		val_der = datos_jugador.get(col_der, 0)
		try:
			val_der = pd.to_numeric(val_der, errors='coerce')
			val_der = 0.0 if pd.isna(val_der) else round(float(val_der), 1)
		except (ValueError, TypeError):
			val_der = 0.0
		jugador_dict[col_der] = val_der
		
		# Izquierda
		val_izq = datos_jugador.get(col_izq, 0)
		try:
			val_izq = pd.to_numeric(val_izq, errors='coerce')
			val_izq = 0.0 if pd.isna(val_izq) else round(float(val_izq), 1)
		except (ValueError, TypeError):
			val_izq = 0.0
		jugador_dict[col_izq] = val_izq
	
	# Procesar métricas totales
	for col_total in columnas_totales:
		val_total = datos_jugador.get(col_total, 0)
		try:
			val_total = pd.to_numeric(val_total, errors='coerce')
			val_total = 0.0 if pd.isna(val_total) else round(float(val_total), 1)
		except (ValueError, TypeError):
			val_total = 0.0
		jugador_dict[col_total] = val_total
	
	return jugador_dict

@st.cache_data(ttl=CACHE_TTL['selecciones'])
def crear_hash_jugador(datos_jugador):
	"""Crea hash único para datos del jugador para optimizar cache"""
	# Convertir Series a dict para hashear
	if hasattr(datos_jugador, 'to_dict'):
		datos_dict = datos_jugador.to_dict()
	else:
		datos_dict = dict(datos_jugador)
	
	# Crear hash único basado en los datos
	datos_str = json.dumps(datos_dict, sort_keys=True, default=str)
	hash_obj = hashlib.md5(datos_str.encode())
	return hash_obj.hexdigest()

def limpiar_cache_si_cambio(jugador, categoria):
	"""Limpia cache si hay cambio en la selección"""
	if (st.session_state.get('ultimo_jugador') != jugador or 
		st.session_state.get('ultima_categoria') != categoria):
		# Limpiar cache de métricas al cambiar selección
		st.session_state.metricas_cache = {}
		return True
	return False

@st.cache_data(ttl=CACHE_TTL['estadisticas'])
def calcular_zscores_automaticos(df_categoria, metricas_zscore):
	"""
	Calcula Z-Scores automáticamente basado en la población actual
	
	Args:
		df_categoria: DataFrame filtrado por categoría
		metricas_zscore: Dict con mapeo de métricas para Z-Score
		
	Returns:
		Dict con estadísticas: {metrica: {'media': float, 'std': float}}
	"""
	estadisticas = {}
	
	# Filtrar solo jugadores (excluir filas de resumen)
	df_limpio = df_categoria[
		(~df_categoria['Deportista'].str.contains('RIESGO|MEDIA|TOTAL|SD', case=False, na=False)) &
		(df_categoria['Deportista'].notna())
	].copy()
	
	for metrica_original, metrica_label in metricas_zscore.items():
		if metrica_original in df_limpio.columns:
			# Convertir a numérico y eliminar valores nulos
			valores = pd.to_numeric(df_limpio[metrica_original], errors='coerce').dropna()
			
			if len(valores) >= 3:  # Mínimo 3 valores para estadísticas confiables
				media = valores.mean()
				std = valores.std(ddof=1)  # Desviación estándar muestral
				
				estadisticas[metrica_original] = {
					'media': round(media, 2),
					'std': round(std, 2),
					'n': len(valores),
					'label': metrica_label
				}
	
	return estadisticas

@st.cache_data(ttl=CACHE_TTL['estadisticas'])
def calcular_zscore_jugador(valor_jugador, media_poblacion, std_poblacion):
	"""
	Calcula Z-Score individual para un jugador
	
	Args:
		valor_jugador: Valor del jugador para la métrica
		media_poblacion: Media de la población de referencia
		std_poblacion: Desviación estándar de la población
		
	Returns:
		float: Z-Score calculado
	"""
	if pd.isna(valor_jugador) or std_poblacion == 0:
		return None
	
	zscore = (valor_jugador - media_poblacion) / std_poblacion
	return round(zscore, 2)

@st.cache_data(ttl=CACHE_TTL['estadisticas'])
def interpretar_zscore_clinico(zscore_valor):
	"""
	Interpreta Z-Score con banderas clínicas y percentiles aproximados
	
	Args:
		zscore_valor: Valor del Z-Score
		
	Returns:
		Dict con interpretación clínica
	"""
	if zscore_valor is None or pd.isna(zscore_valor):
		return {
			'interpretacion': 'Sin datos',
			'color': 'gray',
			'percentil': None,
			'categoria': 'N/A'
		}
	
	# Interpretación basada en distribución normal estándar
	if zscore_valor >= 2.0:
		return {
			'interpretacion': 'Excepcional (>97.5%)',
			'color': '#22c55e',  # Verde brillante
			'percentil': '>97.5',
			'categoria': 'Excelente'
		}
	elif zscore_valor >= 1.0:
		return {
			'interpretacion': 'Superior (84-97.5%)',
			'color': '#16a34a',  # Verde
			'percentil': '84-97.5',
			'categoria': 'Bueno'
		}
	elif zscore_valor >= 0.0:
		return {
			'interpretacion': 'Promedio Alto (50-84%)',
			'color': '#fbbf24',  # Amarillo
			'percentil': '50-84',
			'categoria': 'Promedio+'
		}
	elif zscore_valor >= -1.0:
		return {
			'interpretacion': 'Promedio Bajo (16-50%)',
			'color': '#f59e0b',  # Naranja
			'percentil': '16-50',
			'categoria': 'Promedio-'
		}
	elif zscore_valor >= -2.0:
		return {
			'interpretacion': 'Inferior (2.5-16%)',
			'color': '#ef4444',  # Rojo
			'percentil': '2.5-16',
			'categoria': 'Bajo'
		}
	else:
		return {
			'interpretacion': 'Muy Inferior (<2.5%)',
			'color': '#dc2626',  # Rojo oscuro
			'percentil': '<2.5',
			'categoria': 'Crítico'
		}

@st.cache_data(ttl=CACHE_TTL['preparacion_datos'])
def generar_zscores_jugador(datos_jugador, estadisticas_poblacion, metricas_zscore):
	"""
	Genera todos los Z-Scores para un jugador específico
	
	Args:
		datos_jugador: Series o dict con datos del jugador
		estadisticas_poblacion: Dict con estadísticas de la población
		metricas_zscore: Dict con mapeo de métricas
		
	Returns:
		Dict con Z-Scores y sus interpretaciones
	"""
	zscores_jugador = {}
	
	for metrica_original, metrica_label in metricas_zscore.items():
		if metrica_original in estadisticas_poblacion and metrica_original in datos_jugador:
			valor_jugador = datos_jugador.get(metrica_original)
			stats = estadisticas_poblacion[metrica_original]
			
			# Calcular Z-Score
			zscore = calcular_zscore_jugador(
				valor_jugador, 
				stats['media'], 
				stats['std']
			)
			
			# Interpretar clínicamente
			interpretacion = interpretar_zscore_clinico(zscore)
			
			zscores_jugador[metrica_label] = {
				'valor_original': valor_jugador,
				'zscore': zscore,
				'interpretacion': interpretacion,
				'media_poblacion': stats['media'],
				'std_poblacion': stats['std'],
				'n_poblacion': stats['n']
			}
	
	return zscores_jugador

@st.cache_data(ttl=CACHE_TTL['preparacion_datos'])
def calcular_metricas_bilaterales_promedio(datos_jugador):
	"""
	Calcula promedios de métricas bilaterales para simplificar el radar
	
	Args:
		datos_jugador: Series o dict con datos del jugador
		
	Returns:
		Dict con métricas promediadas
	"""
	metricas_promedio = {}
	
	# CUAD promedio
	cuad_der = datos_jugador.get('CUAD DER (N)', 0)
	cuad_izq = datos_jugador.get('CUAD IZQ (N)', 0)
	if cuad_der > 0 and cuad_izq > 0:
		metricas_promedio['CUAD_PROMEDIO'] = (cuad_der + cuad_izq) / 2
	
	# WOLLIN promedio  
	wollin_der = datos_jugador.get('WOLLIN DER', 0)
	wollin_izq = datos_jugador.get('WOLLIN IZQ', 0)
	if wollin_der > 0 and wollin_izq > 0:
		metricas_promedio['WOLLIN_PROMEDIO'] = (wollin_der + wollin_izq) / 2
	
	# === MÉTRICAS DE MOVILIDAD ===
	# AKE promedio
	ake_der = datos_jugador.get('AKE DER', 0)
	ake_izq = datos_jugador.get('AKE IZQ', 0)
	if ake_der > 0 and ake_izq > 0:
		metricas_promedio['AKE_PROMEDIO'] = (ake_der + ake_izq) / 2
	
	# THOMAS promedio
	thomas_der = datos_jugador.get('THOMAS DER', 0)
	thomas_izq = datos_jugador.get('THOMAS IZQ', 0)
	if thomas_der > 0 and thomas_izq > 0:
		metricas_promedio['THOMAS_PROMEDIO'] = (thomas_der + thomas_izq) / 2
	
	# LUNGE promedio
	lunge_der = datos_jugador.get('LUNGE DER', 0)
	lunge_izq = datos_jugador.get('LUNGE IZQ', 0)
	if lunge_der > 0 and lunge_izq > 0:
		metricas_promedio['LUNGE_PROMEDIO'] = (lunge_der + lunge_izq) / 2
	
	return metricas_promedio

@st.cache_data(ttl=CACHE_TTL['estadisticas'])
def calcular_zscores_radar_simple(df_categoria, metricas_radar_simple):
	"""
	Calcula Z-Scores para el radar simplificado (5 métricas máximo)
	
	Args:
		df_categoria: DataFrame filtrado por categoría
		metricas_radar_simple: Dict con métricas simplificadas
		
	Returns:
		Dict con estadísticas para radar simple
	"""
	estadisticas = {}
	
	# Filtrar solo jugadores
	df_limpio = df_categoria[
		(~df_categoria['Deportista'].str.contains('RIESGO|MEDIA|TOTAL|SD', case=False, na=False)) &
		(df_categoria['Deportista'].notna())
	].copy()
	
	# Calcular estadísticas para métricas directas (totales)
	metricas_directas = {
		'F PICO (IMTP) (N)': 'IMTP',
		'FP (CMJ) (N)': 'CMJ Propulsiva',
		'FF (CMJ) (N)': 'CMJ Frenado'
	}
	
	for metrica_col, metrica_label in metricas_directas.items():
		if metrica_col in df_limpio.columns:
			valores = pd.to_numeric(df_limpio[metrica_col], errors='coerce').dropna()
			if len(valores) >= 3:
				estadisticas[metrica_col] = {
					'media': round(valores.mean(), 2),
					'std': round(valores.std(ddof=1), 2),
					'n': len(valores),
					'label': metrica_label
				}
	
	# Calcular estadísticas para métricas bilaterales (promedios)
	# CUAD promedio
	cuad_der_vals = pd.to_numeric(df_limpio.get('CUAD DER (N)', []), errors='coerce').dropna()
	cuad_izq_vals = pd.to_numeric(df_limpio.get('CUAD IZQ (N)', []), errors='coerce').dropna()
	if len(cuad_der_vals) >= 3 and len(cuad_izq_vals) >= 3:
		cuad_promedios = (cuad_der_vals + cuad_izq_vals) / 2
		estadisticas['CUAD_PROMEDIO'] = {
			'media': round(cuad_promedios.mean(), 2),
			'std': round(cuad_promedios.std(ddof=1), 2),
			'n': len(cuad_promedios),
			'label': 'CUAD'
		}
	
	# WOLLIN promedio
	wollin_der_vals = pd.to_numeric(df_limpio.get('WOLLIN DER', []), errors='coerce').dropna()
	wollin_izq_vals = pd.to_numeric(df_limpio.get('WOLLIN IZQ', []), errors='coerce').dropna()
	if len(wollin_der_vals) >= 3 and len(wollin_izq_vals) >= 3:
		wollin_promedios = (wollin_der_vals + wollin_izq_vals) / 2
		estadisticas['WOLLIN_PROMEDIO'] = {
			'media': round(wollin_promedios.mean(), 2),
			'std': round(wollin_promedios.std(ddof=1), 2),
			'n': len(wollin_promedios),
			'label': 'ISQ Wollin'
		}
	
	# === MÉTRICAS DE MOVILIDAD ===
	# AKE promedio
	ake_der_vals = pd.to_numeric(df_limpio.get('AKE DER', []), errors='coerce').dropna()
	ake_izq_vals = pd.to_numeric(df_limpio.get('AKE IZQ', []), errors='coerce').dropna()
	if len(ake_der_vals) >= 3 and len(ake_izq_vals) >= 3:
		ake_promedios = (ake_der_vals + ake_izq_vals) / 2
		estadisticas['AKE_PROMEDIO'] = {
			'media': round(ake_promedios.mean(), 2),
			'std': round(ake_promedios.std(ddof=1), 2),
			'n': len(ake_promedios),
			'label': 'AKE'
		}
	
	# THOMAS promedio
	thomas_der_vals = pd.to_numeric(df_limpio.get('THOMAS DER', []), errors='coerce').dropna()
	thomas_izq_vals = pd.to_numeric(df_limpio.get('THOMAS IZQ', []), errors='coerce').dropna()
	if len(thomas_der_vals) >= 3 and len(thomas_izq_vals) >= 3:
		thomas_promedios = (thomas_der_vals + thomas_izq_vals) / 2
		estadisticas['THOMAS_PROMEDIO'] = {
			'media': round(thomas_promedios.mean(), 2),
			'std': round(thomas_promedios.std(ddof=1), 2),
			'n': len(thomas_promedios),
			'label': 'THOMAS'
		}
	
	# LUNGE promedio
	lunge_der_vals = pd.to_numeric(df_limpio.get('LUNGE DER', []), errors='coerce').dropna()
	lunge_izq_vals = pd.to_numeric(df_limpio.get('LUNGE IZQ', []), errors='coerce').dropna()
	if len(lunge_der_vals) >= 3 and len(lunge_izq_vals) >= 3:
		lunge_promedios = (lunge_der_vals + lunge_izq_vals) / 2
		estadisticas['LUNGE_PROMEDIO'] = {
			'media': round(lunge_promedios.mean(), 2),
			'std': round(lunge_promedios.std(ddof=1), 2),
			'n': len(lunge_promedios),
			'label': 'LUNGE'
		}
	
	return estadisticas

@st.cache_data(ttl=CACHE_TTL['preparacion_datos'])
def generar_zscores_radar_simple(datos_jugador, estadisticas_poblacion, metricas_radar_simple):
	"""
	Genera Z-Scores para el radar simplificado
	
	Args:
		datos_jugador: Series o dict con datos del jugador
		estadisticas_poblacion: Dict con estadísticas de la población
		metricas_radar_simple: Dict con mapeo de métricas simplificadas
		
	Returns:
		Dict con Z-Scores para radar simple
	"""
	zscores_radar = {}
	
	# Calcular promedios bilaterales del jugador
	metricas_promedio = calcular_metricas_bilaterales_promedio(datos_jugador)
	
	# Combinar datos originales con promedios calculados
	datos_completos = dict(datos_jugador)
	datos_completos.update(metricas_promedio)
	
	# Calcular Z-Scores para cada métrica del radar
	for metrica_key, metrica_label in metricas_radar_simple.items():
		if metrica_key in estadisticas_poblacion and metrica_key in datos_completos:
			valor_jugador = datos_completos[metrica_key]
			stats = estadisticas_poblacion[metrica_key]
			
			# Calcular Z-Score
			zscore = calcular_zscore_jugador(
				valor_jugador,
				stats['media'],
				stats['std']
			)
			
			if zscore is not None:
				zscores_radar[metrica_label] = {
					'zscore': zscore,
					'valor_original': valor_jugador,
					'media_poblacion': stats['media']
				}
	
	return zscores_radar

@st.cache_data(ttl=CACHE_TTL['estadisticas'])
def calcular_estadisticas_distribucion_grupal(df_categoria, metricas_radar_simple):
	"""
	Calcula estadísticas completas para distribución grupal (media, min, max)
	
	Args:
		df_categoria: DataFrame filtrado por categoría
		metricas_radar_simple: Dict con métricas simplificadas
		
	Returns:
		Dict con estadísticas completas para distribución grupal
	"""
	estadisticas = {}
	
	# Filtrar solo jugadores
	df_limpio = df_categoria[
		(~df_categoria['Deportista'].str.contains('RIESGO|MEDIA|TOTAL|SD', case=False, na=False)) &
		(df_categoria['Deportista'].notna())
	].copy()
	
	# Calcular estadísticas para métricas directas (totales)
	metricas_directas = {
		'F PICO (IMTP) (N)': 'IMTP Total',
		'FP (CMJ) (N)': 'CMJ FP Total',
		'FF (CMJ) (N)': 'CMJ FF Total'
	}
	
	for metrica_col, metrica_label in metricas_directas.items():
		if metrica_col in df_limpio.columns:
			valores = pd.to_numeric(df_limpio[metrica_col], errors='coerce').dropna()
			if len(valores) >= 3:
				estadisticas[metrica_col] = {
					'media': round(valores.mean(), 2),
					'std': round(valores.std(ddof=1), 2),
					'minimo': round(valores.min(), 2),
					'maximo': round(valores.max(), 2),
					'n': len(valores),
					'label': metrica_label
				}
	
	# Calcular estadísticas para métricas bilaterales (promedios)
	# CUAD promedio
	cuad_der_vals = pd.to_numeric(df_limpio.get('CUAD DER (N)', []), errors='coerce').dropna()
	cuad_izq_vals = pd.to_numeric(df_limpio.get('CUAD IZQ (N)', []), errors='coerce').dropna()
	if len(cuad_der_vals) >= 3 and len(cuad_izq_vals) >= 3:
		cuad_promedios = (cuad_der_vals + cuad_izq_vals) / 2
		estadisticas['CUAD_PROMEDIO'] = {
			'media': round(cuad_promedios.mean(), 2),
			'std': round(cuad_promedios.std(ddof=1), 2),
			'minimo': round(cuad_promedios.min(), 2),
			'maximo': round(cuad_promedios.max(), 2),
			'n': len(cuad_promedios),
			'label': 'CUAD'
		}
	
	# WOLLIN promedio
	wollin_der_vals = pd.to_numeric(df_limpio.get('WOLLIN DER', []), errors='coerce').dropna()
	wollin_izq_vals = pd.to_numeric(df_limpio.get('WOLLIN IZQ', []), errors='coerce').dropna()
	if len(wollin_der_vals) >= 3 and len(wollin_izq_vals) >= 3:
		wollin_promedios = (wollin_der_vals + wollin_izq_vals) / 2
		estadisticas['WOLLIN_PROMEDIO'] = {
			'media': round(wollin_promedios.mean(), 2),
			'std': round(wollin_promedios.std(ddof=1), 2),
			'minimo': round(wollin_promedios.min(), 2),
			'maximo': round(wollin_promedios.max(), 2),
			'n': len(wollin_promedios),
			'label': 'ISQ Wollin'
		}
	
	# TRIPLE SALTO promedio
	triple_der_vals = pd.to_numeric(df_limpio.get('TRIPLE SALTO DER', []), errors='coerce').dropna()
	triple_izq_vals = pd.to_numeric(df_limpio.get('TRIPLE SALTO IZQ', []), errors='coerce').dropna()
	if len(triple_der_vals) >= 3 and len(triple_izq_vals) >= 3:
		triple_promedios = (triple_der_vals + triple_izq_vals) / 2
		estadisticas['TRIPLE_SALTO_PROMEDIO'] = {
			'media': round(triple_promedios.mean(), 2),
			'std': round(triple_promedios.std(ddof=1), 2),
			'minimo': round(triple_promedios.min(), 2),
			'maximo': round(triple_promedios.max(), 2),
			'n': len(triple_promedios),
			'label': 'TRIPLE SALTO'
		}
	
	return estadisticas
