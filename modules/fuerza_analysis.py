"""
Módulo de análisis de fuerza
"""

import streamlit as st
import pandas as pd
from visualizations.charts import crear_grafico_multifuerza, crear_radar_zscore, crear_radar_zscore_automatico, crear_radar_zscore_simple, crear_grafico_multifuerza_grupal, crear_radar_zscore_grupal, crear_grafico_distribucion_grupal
from utils.data_utils import (
	procesar_datos_categoria, calcular_estadisticas_categoria, preparar_datos_jugador,
	calcular_zscores_automaticos, generar_zscores_jugador, calcular_zscores_radar_simple, generar_zscores_radar_simple,
	calcular_estadisticas_completas_categoria, preparar_datos_jugador_completo, calcular_estadisticas_distribucion_grupal
)
from config.settings import PLOTLY_CONFIG, METRICAS_ZSCORE_FUERZA, METRICAS_ZSCORE_RADAR_SIMPLE

def analizar_fuerza(df, datos_jugador, jugador, categoria):
	"""Realiza el análisis completo de fuerza"""
	
	# === Selección de métricas de fuerza - EXPANDIDAS ===
	metricas_disponibles = ["CUAD", "WOLLIN", "IMTP", "CMJ Propulsiva", "CMJ Frenado", "TRIPLE SALTO", "IMTP Total", "CMJ FP Total", "CMJ FF Total"]
	metricas_display = ["CUAD", "WOLLIN", "IMTP", "CMJ Propulsiva", "CMJ Frenado", "TRIPLE SALTO", "IMTP Total", "CMJ FP Total", "CMJ FF Total"]
	metricas_columnas = {
		"CUAD": ("CUAD DER (N)", "CUAD IZQ (N)"),
		"WOLLIN": ("WOLLIN DER", "WOLLIN IZQ"),
		"IMTP": ("F PICO DER (IMTP) (N)", "F PICO IZQ (IMTP) (N)"),
		"CMJ Propulsiva": ("FP DER (CMJ) (N)", "FP IZQ (CMJ) (N)"),
		"CMJ Frenado": ("FF DER (CMJ) (N)", "FF IZQ (CMJ) (N)"),
		"TRIPLE SALTO": ("TRIPLE SALTO DER", "TRIPLE SALTO IZQ"),
		"IMTP Total": ("F PICO (IMTP) (N)", "F PICO (IMTP) (N)"),  # Valor total bilateral
		"CMJ FP Total": ("FP (CMJ) (N)", "FP (CMJ) (N)"),  # Valor total bilateral
		"CMJ FF Total": ("FF (CMJ) (N)", "FF (CMJ) (N)")   # Valor total bilateral
	}

	metricas_seleccionadas_display = st.multiselect(
		"Selección de Métricas - Selecciona las evaluaciones para el análisis:",
		metricas_disponibles,
		default=["CUAD", "WOLLIN", "IMTP", "CMJ Propulsiva"]
	)
	
	# Convertir de display a nombres reales
	metricas_seleccionadas = []
	for metrica_display in metricas_seleccionadas_display:
		for i, display in enumerate(metricas_disponibles):
			if metrica_display == display:
				metricas_seleccionadas.append(metricas_display[i])

	if metricas_seleccionadas:
		# Espaciado entre selector y gráfico
		st.markdown("<br>", unsafe_allow_html=True)
		
		# Optimización con cache - crear hash del jugador
		datos_jugador_dict = datos_jugador.to_dict() if hasattr(datos_jugador, 'to_dict') else dict(datos_jugador)
		
		# Generar gráfico con cache optimizado
		fig_multifuerza = crear_grafico_multifuerza(datos_jugador_dict, tuple(metricas_seleccionadas), metricas_columnas)
		
		# Mostrar gráfico con animación
		st.markdown("""
		<div style="animation: fadeInUp 0.8s ease-out;">
		""", unsafe_allow_html=True)
		
		st.plotly_chart(fig_multifuerza, use_container_width=True, config=PLOTLY_CONFIG)
		
		st.markdown("</div>", unsafe_allow_html=True)
		
		# === RADAR Z-SCORE SIMPLIFICADO ===
		st.markdown("<br><br>", unsafe_allow_html=True)
		
		# Header para el radar simplificado
		st.markdown(f"""
		<div style='background: linear-gradient(90deg, rgba(220, 38, 38, 0.8), rgba(17, 24, 39, 0.8));
					border-left: 4px solid rgba(220, 38, 38, 1); padding: 15px; border-radius: 8px;'>
			<h4 style='margin: 0; color: white; font-family: "Source Sans Pro", sans-serif; font-weight: 600; font-size: 1.5rem; line-height: 1.2; padding: 0.75rem 0 1rem;'>
				Comparación vs Grupo
			</h4>
		</div>
		""", unsafe_allow_html=True)
		
		# Espaciado para mejorar el estilo visual
		st.markdown("<br>", unsafe_allow_html=True)
		
		# Calcular estadísticas poblacionales para radar simplificado
		with st.spinner("Calculando estadísticas para radar..."):
			df_categoria = procesar_datos_categoria(df, categoria)
			estadisticas_radar = calcular_zscores_radar_simple(df_categoria, METRICAS_ZSCORE_RADAR_SIMPLE)
		
		# Generar Z-Scores simplificados del jugador
		if estadisticas_radar:
			zscores_radar = generar_zscores_radar_simple(datos_jugador, estadisticas_radar, METRICAS_ZSCORE_RADAR_SIMPLE)
			
			# Radar chart simplificado - pantalla completa
			fig_radar_simple = crear_radar_zscore_simple(zscores_radar, jugador)
			
			radar_config = PLOTLY_CONFIG.copy()
			radar_config['toImageButtonOptions'].update({
				'filename': f'radar_simple_{jugador}_{categoria}',
				'height': 600,
				'width': 800
			})
			
			st.plotly_chart(fig_radar_simple, use_container_width=True, config=radar_config)
			
			# Información resumida debajo del radar
			if zscores_radar:
				# Crear métricas en columnas
				cols = st.columns(len(zscores_radar))
				
				for i, (metrica, data) in enumerate(zscores_radar.items()):
					with cols[i]:
						zscore = data['zscore']
						valor = data['valor_original']
						
						# Determinar color según Z-Score
						if zscore >= 1.0:
							color = "#22c55e"  # Verde
							categoria = "Superior"
						elif zscore >= 0.0:
							color = "#fbbf24"  # Amarillo
							categoria = "Promedio+"
						elif zscore >= -1.0:
							color = "#f59e0b"  # Naranja
							categoria = "Promedio-"
						else:
							color = "#ef4444"  # Rojo
							categoria = "Inferior"
						
						st.markdown(f"""
						<div style='text-align: center; padding: 10px; background: rgba(31, 41, 55, 0.6); 
									border-radius: 8px; border-top: 3px solid {color};'>
							<h5 style='margin: 0; color: white; font-size: 12px;'>{metrica}</h5>
							<p style='margin: 2px 0; color: {color}; font-weight: bold; font-size: 14px;'>
								{zscore:.1f}
							</p>
							<p style='margin: 0; color: rgba(255,255,255,0.7); font-size: 10px;'>
								{categoria}
							</p>
						</div>
						""", unsafe_allow_html=True)
		
		else:
			# Fallback si no hay datos suficientes
			st.warning("Datos insuficientes para Z-Scores. Se requieren al menos 3 jugadores en la categoría.")
			
			# Mostrar mensaje centrado
			col1, col_center, col2 = st.columns([1, 2, 1])
			with col_center:
				st.info("Agregue más jugadores a la categoría para habilitar el análisis Z-Score.")
		


		# === TABLA COMPARATIVA ===
		st.markdown(f"#### Tabla - {jugador}")

		# Columnas de fuerza que queremos analizar - EXPANDIDAS
		columnas_tabla = {
			"CUAD DER (N)": "CUAD IZQ (N)",
			"WOLLIN DER": "WOLLIN IZQ",
			"F PICO DER (IMTP) (N)": "F PICO IZQ (IMTP) (N)",
			"FP DER (CMJ) (N)": "FP IZQ (CMJ) (N)",
			"FF DER (CMJ) (N)": "FF IZQ (CMJ) (N)",
			"TRIPLE SALTO DER": "TRIPLE SALTO IZQ"
		}
		
		# Agregar métricas totales como columnas individuales
		columnas_totales = ["F PICO (IMTP) (N)", "FP (CMJ) (N)", "FF (CMJ) (N)"]

		# CALCULAR ESTADÍSTICAS GRUPALES USANDO LA CATEGORÍA BASE CON MÁS JUGADORES
		# Encontrar la categoría con más jugadores para usar como referencia
		categorias_disponibles = df['categoria'].value_counts()
		categoria_base = categorias_disponibles.index[0]  # La categoría con más jugadores
		
		# Usar la categoría base para estadísticas grupales (FIJAS)
		df_categoria_base = procesar_datos_categoria(df, categoria_base)
		estadisticas_grupales = calcular_estadisticas_completas_categoria(df_categoria_base, columnas_tabla, columnas_totales)
		
		# Obtener número de jugadores para los nombres de las filas
		n_jugadores_categoria = estadisticas_grupales['n_jugadores']
		
		# PREPARAR SOLO LOS DATOS DEL JUGADOR SELECCIONADO (DINÁMICO)
		jugador_dict = preparar_datos_jugador_completo(datos_jugador_dict, columnas_tabla, columnas_totales)

		# Ordenar columnas como pares + totales
		column_order = []
		for der, izq in columnas_tabla.items():
			column_order.extend([der, izq])
		column_order.extend(columnas_totales)

		# Validar que todas las columnas existan en los diccionarios antes de crear DataFrame
		columnas_validas = []
		for col in column_order:
			if col in jugador_dict and col in estadisticas_grupales['media'] and col in estadisticas_grupales['std']:
				columnas_validas.append(col)
			else:
				st.warning(f"⚠️ Columna '{col}' no encontrada en los datos")

		# Crear DataFrame comparativo original solo con columnas válidas
		if columnas_validas:
			df_comparativo = pd.DataFrame([
				jugador_dict,
				estadisticas_grupales['media'],
				estadisticas_grupales['std']
			])[columnas_validas]
		else:
			st.error("❌ No se encontraron columnas válidas para la tabla")
			return
		# Nombres simplificados para las filas
		n_jugadores = estadisticas_grupales['n_jugadores']
		df_comparativo.index = [f"{jugador}", "Media", "Desviación Estándar"]
		
		# Transponer tabla para mejor visualización y exportación PDF
		df_transpuesto = df_comparativo.T
		df_transpuesto.index.name = "Métrica"
		
		# Mostrar tabla transpuesta con estilo optimizado
		st.dataframe(
			df_transpuesto.style.format("{:.1f}").apply(
				lambda x: [
					'background-color: rgba(220, 38, 38, 0.15); font-weight: bold;',  # Columna jugador
					'background-color: rgba(255, 255, 255, 0.08);',  # Columna media
					'background-color: rgba(59, 130, 246, 0.15);'    # Columna desv. est.
				], axis=1
			).set_table_styles([
				{'selector': 'th.col_heading', 'props': 'background-color: rgba(220, 38, 38, 0.3); color: white; font-weight: bold;'},
				{'selector': 'th.row_heading', 'props': 'background-color: rgba(31, 41, 55, 0.8); color: white; font-weight: bold; text-align: left;'},
				{'selector': 'td', 'props': 'text-align: center; padding: 8px;'}
			]),
			use_container_width=True
		)
		
	else:
		st.info("Selecciona al menos una métrica para visualizar el gráfico.")

def analizar_fuerza_grupal(df, categoria):
	"""Realiza el análisis completo de fuerza GRUPAL - métricas agregadas"""
	
	# Mapeo de nombres técnicos a nombres amigables
	mapeo_categorias = {
		"Evaluacion_2910": "Primer Equipo",
		"Reserva": "Reserva",
		"4ta": "4ta División"
	}
	categoria_display = mapeo_categorias.get(categoria, categoria)
	
	# === Selección de métricas de fuerza - EXPANDIDAS (IGUAL QUE INDIVIDUAL) ===
	metricas_disponibles = ["CUAD", "WOLLIN", "IMTP", "CMJ Propulsiva", "CMJ Frenado", "TRIPLE SALTO", "IMTP Total", "CMJ FP Total", "CMJ FF Total"]
	metricas_display = ["CUAD", "WOLLIN", "IMTP", "CMJ Propulsiva", "CMJ Frenado", "TRIPLE SALTO", "IMTP Total", "CMJ FP Total", "CMJ FF Total"]
	metricas_columnas = {
		"CUAD": ("CUAD DER (N)", "CUAD IZQ (N)"),
		"WOLLIN": ("WOLLIN DER", "WOLLIN IZQ"),
		"IMTP": ("F PICO DER (IMTP) (N)", "F PICO IZQ (IMTP) (N)"),
		"CMJ Propulsiva": ("FP DER (CMJ) (N)", "FP IZQ (CMJ) (N)"),
		"CMJ Frenado": ("FF DER (CMJ) (N)", "FF IZQ (CMJ) (N)"),
		"TRIPLE SALTO": ("TRIPLE SALTO DER", "TRIPLE SALTO IZQ"),
		"IMTP Total": ("F PICO (IMTP) (N)", "F PICO (IMTP) (N)"),  # Valor total bilateral
		"CMJ FP Total": ("FP (CMJ) (N)", "FP (CMJ) (N)"),  # Valor total bilateral
		"CMJ FF Total": ("FF (CMJ) (N)", "FF (CMJ) (N)")   # Valor total bilateral
	}

	metricas_seleccionadas_display = st.multiselect(
		"Selección de Métricas - Selecciona las evaluaciones para el análisis grupal:",
		metricas_disponibles,
		default=["CUAD", "WOLLIN", "IMTP", "CMJ Propulsiva"]
	)
	
	# Convertir de display a nombres reales
	metricas_seleccionadas = []
	for metrica_display in metricas_seleccionadas_display:
		for i, display in enumerate(metricas_disponibles):
			if metrica_display == display:
				metricas_seleccionadas.append(metricas_display[i])

	if metricas_seleccionadas:
		# Espaciado entre selector y gráfico
		st.markdown("<br>", unsafe_allow_html=True)
		
		# Procesar datos de la categoría para obtener estadísticas grupales
		df_categoria = procesar_datos_categoria(df, categoria)
		
		# Calcular estadísticas grupales para las métricas seleccionadas
		estadisticas_grupales = {}
		for metrica in metricas_seleccionadas:
			col_der, col_izq = metricas_columnas[metrica]
			
			# Para métricas totales, usar solo una columna
			if metrica in ["IMTP Total", "CMJ FP Total", "CMJ FF Total"]:
				col_total = col_der  # Usar la primera columna
				if col_total in df_categoria.columns:
					valores_total = pd.to_numeric(df_categoria[col_total], errors='coerce').dropna()
					if len(valores_total) > 0:
						estadisticas_grupales[metrica] = {
							'media_total': round(valores_total.mean(), 1),
							'std_total': round(valores_total.std(), 1) if len(valores_total) > 1 else 0.0,
							'n_jugadores': len(valores_total)
						}
			else:
				# Para métricas bilaterales, calcular medias de cada lado
				valores_der = pd.to_numeric(df_categoria.get(col_der, []), errors='coerce').dropna()
				valores_izq = pd.to_numeric(df_categoria.get(col_izq, []), errors='coerce').dropna()
				
				if len(valores_der) > 0 and len(valores_izq) > 0:
					estadisticas_grupales[metrica] = {
						'media_der': round(valores_der.mean(), 1),
						'media_izq': round(valores_izq.mean(), 1),
						'std_der': round(valores_der.std(), 1) if len(valores_der) > 1 else 0.0,
						'std_izq': round(valores_izq.std(), 1) if len(valores_izq) > 1 else 0.0,
						'n_jugadores': min(len(valores_der), len(valores_izq))
					}
		
		# Generar gráfico grupal con cache optimizado
		fig_multifuerza_grupal = crear_grafico_multifuerza_grupal(estadisticas_grupales, tuple(metricas_seleccionadas), categoria_display)
		
		# Mostrar gráfico con animación
		st.markdown("""
		<div style="animation: fadeInUp 0.8s ease-out;">
		""", unsafe_allow_html=True)
		
		st.plotly_chart(fig_multifuerza_grupal, use_container_width=True, config=PLOTLY_CONFIG)
		
		st.markdown("</div>", unsafe_allow_html=True)
		
		# === DISTRIBUCIÓN GRUPAL ===
		st.markdown("<br><br>", unsafe_allow_html=True)
		
		# Header para la distribución grupal - EXACTAMENTE IGUAL AL INDIVIDUAL
		st.markdown(f"""
		<div style='background: linear-gradient(90deg, rgba(220, 38, 38, 0.8), rgba(17, 24, 39, 0.8));
					border-left: 4px solid rgba(220, 38, 38, 1); padding: 15px; border-radius: 8px;'>
			<h4 style='margin: 0; color: white; font-family: "Source Sans Pro", sans-serif; font-weight: 600; font-size: 1.5rem; line-height: 1.2; padding: 0.75rem 0 1rem;'>
				Distribución del Grupo
			</h4>
		</div>
		""", unsafe_allow_html=True)
		
		# Espaciado para mejorar el estilo visual
		st.markdown("<br>", unsafe_allow_html=True)
		
		# Calcular estadísticas poblacionales para distribución grupal
		with st.spinner("Calculando distribución grupal..."):
			estadisticas_radar_grupal = calcular_estadisticas_distribucion_grupal(df_categoria, METRICAS_ZSCORE_RADAR_SIMPLE)
		
		# Generar gráfico de distribución grupal (reemplaza al radar)
		if estadisticas_radar_grupal:
			# Gráfico de distribución con barras y rangos
			fig_distribucion_grupal = crear_grafico_distribucion_grupal(estadisticas_radar_grupal, categoria_display)
			
			distribucion_config = PLOTLY_CONFIG.copy()
			distribucion_config['toImageButtonOptions'].update({
				'filename': f'distribucion_grupal_{categoria}',
				'height': 600,
				'width': 800
			})
			
			st.plotly_chart(fig_distribucion_grupal, use_container_width=True, config=distribucion_config)
			
			# Información resumida debajo del gráfico de distribución
			if estadisticas_radar_grupal:
				# Crear métricas en columnas
				metricas_info = []
				orden_metricas = ['CUAD', 'ISQ Wollin', 'IMTP Total', 'CMJ FP Total', 'CMJ FF Total', 'TRIPLE SALTO']
				
				for metrica in orden_metricas:
					for metrica_key, stats in estadisticas_radar_grupal.items():
						if stats['label'] == metrica:
							metricas_info.append((metrica, stats['media'], stats['minimo'], stats['maximo']))
							break
				
				if metricas_info:
					cols = st.columns(len(metricas_info))
					
					for i, (metrica, media, minimo, maximo) in enumerate(metricas_info):
						with cols[i]:
							# Color rojo para métricas grupales (igual al individual)
							color = "#dc2626"  # Rojo
							
							st.markdown(f"""
							<div style='text-align: center; padding: 12px; background: rgba(220, 38, 38, 0.15); 
										border-radius: 8px; border-top: 3px solid {color};'>
								<h5 style='margin: 0; color: white; font-size: 13px; font-weight: bold;'>{metrica}</h5>
								<p style='margin: 8px 0; color: {color}; font-weight: bold; font-size: 20px;'>
									{media:.0f}
								</p>
								<p style='margin: 0; color: rgba(255,255,255,0.7); font-size: 11px;'>
									Media Grupal
								</p>
							</div>
							""", unsafe_allow_html=True)
		
		else:
			# Fallback si no hay datos suficientes
			st.warning("Datos insuficientes para análisis grupal. Se requieren al menos 3 jugadores en la categoría.")
			
			# Mostrar mensaje centrado
			col1, col_center, col2 = st.columns([1, 2, 1])
			with col_center:
				st.info("Agregue más jugadores a la categoría para habilitar el análisis grupal.")

		# === TABLA COMPARATIVA GRUPAL ===
		st.markdown(f"#### Tabla - {categoria_display}")

		# Columnas de fuerza que queremos analizar - EXPANDIDAS (IGUAL QUE INDIVIDUAL)
		columnas_tabla = {
			"CUAD DER (N)": "CUAD IZQ (N)",
			"WOLLIN DER": "WOLLIN IZQ",
			"F PICO DER (IMTP) (N)": "F PICO IZQ (IMTP) (N)",
			"FP DER (CMJ) (N)": "FP IZQ (CMJ) (N)",
			"FF DER (CMJ) (N)": "FF IZQ (CMJ) (N)",
			"TRIPLE SALTO DER": "TRIPLE SALTO IZQ"
		}
		
		# Agregar métricas totales como columnas individuales
		columnas_totales = ["F PICO (IMTP) (N)", "FP (CMJ) (N)", "FF (CMJ) (N)"]

		# CALCULAR ESTADÍSTICAS GRUPALES PARA LA CATEGORÍA SELECCIONADA
		estadisticas_grupales_tabla = calcular_estadisticas_completas_categoria(df_categoria, columnas_tabla, columnas_totales)
		
		# Obtener número de jugadores para los nombres de las filas
		n_jugadores_categoria = estadisticas_grupales_tabla['n_jugadores']

		# Ordenar columnas como pares + totales
		column_order = []
		for der, izq in columnas_tabla.items():
			column_order.extend([der, izq])
		column_order.extend(columnas_totales)

		# Validar que todas las columnas existan en los diccionarios antes de crear DataFrame
		columnas_validas = []
		for col in column_order:
			if col in estadisticas_grupales_tabla['media'] and col in estadisticas_grupales_tabla['std']:
				columnas_validas.append(col)
			else:
				st.warning(f"⚠️ Columna '{col}' no encontrada en los datos grupales")

		# Crear DataFrame comparativo grupal solo con columnas válidas
		if columnas_validas:
			df_comparativo_grupal = pd.DataFrame([
				estadisticas_grupales_tabla['media'],
				estadisticas_grupales_tabla['std']
			])[columnas_validas]
		else:
			st.error("❌ No se encontraron columnas válidas para la tabla grupal")
			return
		
		# Nombres para las filas grupales
		df_comparativo_grupal.index = ["Media Grupal", "Desviación Estándar"]
		
		# Transponer tabla para mejor visualización
		df_transpuesto_grupal = df_comparativo_grupal.T
		df_transpuesto_grupal.index.name = "Métrica"
		
		# Mostrar tabla transpuesta con estilo optimizado para análisis grupal
		st.dataframe(
			df_transpuesto_grupal.style.format("{:.1f}").apply(
				lambda x: [
					'background-color: rgba(220, 38, 38, 0.15); font-weight: bold;',  # Columna media grupal
					'background-color: rgba(31, 41, 55, 0.15);'    # Columna desv. est. grupal
				], axis=1
			).set_table_styles([
				{'selector': 'th.col_heading', 'props': 'background-color: rgba(220, 38, 38, 0.3); color: white; font-weight: bold;'},
				{'selector': 'th.row_heading', 'props': 'background-color: rgba(31, 41, 55, 0.8); color: white; font-weight: bold; text-align: left;'},
				{'selector': 'td', 'props': 'text-align: center; padding: 8px;'}
			]),
			use_container_width=True
		)
		
	else:
		st.info("Selecciona al menos una métrica para visualizar el análisis grupal.")
