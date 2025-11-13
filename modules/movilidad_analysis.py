"""
Módulo de análisis de movilidad
"""

import streamlit as st
import pandas as pd
from visualizations.charts import crear_grafico_multimovilidad, crear_radar_zscore_simple_movilidad
from utils.data_utils import (
	procesar_datos_categoria, calcular_estadisticas_categoria, preparar_datos_jugador,
	calcular_zscores_automaticos, generar_zscores_jugador, calcular_zscores_radar_simple, generar_zscores_radar_simple,
	calcular_estadisticas_completas_categoria, preparar_datos_jugador_completo
)
from config.settings import PLOTLY_CONFIG, METRICAS_ZSCORE_MOVILIDAD

def analizar_movilidad(df, datos_jugador, jugador, categoria):
	"""Realiza el análisis completo de movilidad"""
	
	# === Selección de métricas de movilidad ===
	metricas_disponibles = ["AKE", "THOMAS", "LUNGE"]
	metricas_display = ["AKE", "THOMAS", "LUNGE"]
	metricas_columnas = {
		"AKE": ("AKE DER", "AKE IZQ"),
		"THOMAS": ("THOMAS DER", "THOMAS IZQ"),
		"LUNGE": ("LUNGE DER", "LUNGE IZQ")
	}

	metricas_seleccionadas_display = st.multiselect(
		"Selección de Métricas - Selecciona las evaluaciones para el análisis:",
		metricas_disponibles,
		default=["AKE", "THOMAS", "LUNGE"]
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
		fig_multimovilidad = crear_grafico_multimovilidad(datos_jugador_dict, tuple(metricas_seleccionadas), metricas_columnas)
		
		# Mostrar gráfico con animación
		st.markdown("""
		<div style="animation: fadeInUp 0.8s ease-out;">
		""", unsafe_allow_html=True)
		
		st.plotly_chart(fig_multimovilidad, use_container_width=True, config=PLOTLY_CONFIG)
		
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
			estadisticas_radar = calcular_zscores_radar_simple(df_categoria, METRICAS_ZSCORE_MOVILIDAD)
		
		# Generar Z-Scores simplificados del jugador
		if estadisticas_radar:
			zscores_radar = generar_zscores_radar_simple(datos_jugador, estadisticas_radar, METRICAS_ZSCORE_MOVILIDAD)
			
			# Radar chart simplificado - pantalla completa
			fig_radar_simple = crear_radar_zscore_simple_movilidad(zscores_radar, jugador)
			
			radar_config = PLOTLY_CONFIG.copy()
			radar_config['toImageButtonOptions'].update({
				'filename': f'radar_simple_movilidad_{jugador}_{categoria}',
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
							categoria_nivel = "Superior"
						elif zscore >= 0.0:
							color = "#fbbf24"  # Amarillo
							categoria_nivel = "Promedio+"
						elif zscore >= -1.0:
							color = "#f59e0b"  # Naranja
							categoria_nivel = "Promedio-"
						else:
							color = "#ef4444"  # Rojo
							categoria_nivel = "Inferior"
						
						st.markdown(f"""
						<div style='text-align: center; padding: 10px; background: rgba(31, 41, 55, 0.6); 
									border-radius: 8px; border-top: 3px solid {color};'>
							<h5 style='margin: 0; color: white; font-size: 12px;'>{metrica}</h5>
							<p style='margin: 2px 0; color: {color}; font-weight: bold; font-size: 14px;'>
								{zscore:.1f}
							</p>
							<p style='margin: 0; color: rgba(255,255,255,0.7); font-size: 10px;'>
								{categoria_nivel}
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

		# Columnas de movilidad que queremos analizar
		columnas_tabla = {
			"AKE DER": "AKE IZQ",
			"THOMAS DER": "THOMAS IZQ",
			"LUNGE DER": "LUNGE IZQ"
		}
		
		# No hay métricas totales en movilidad
		columnas_totales = []

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

		# Ordenar columnas como pares
		column_order = []
		for der, izq in columnas_tabla.items():
			column_order.extend([der, izq])

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
