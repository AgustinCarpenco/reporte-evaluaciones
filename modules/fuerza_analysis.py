"""
Módulo de análisis de fuerza
"""

import streamlit as st
import pandas as pd
from visualizations.charts import crear_grafico_multifuerza, crear_radar_zscore, crear_radar_zscore_automatico, crear_radar_zscore_simple
from utils.data_utils import (
	procesar_datos_categoria, calcular_estadisticas_categoria, preparar_datos_jugador,
	calcular_zscores_automaticos, generar_zscores_jugador, calcular_zscores_radar_simple, generar_zscores_radar_simple
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
			<h4 style='margin: 0; color: white; font-size: 18px; font-weight: bold;'>
				⚽ Perfil Z-Score - Comparación vs Grupo
			</h4>
			<p style='margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 14px;'>
				Radar simplificado con 5 métricas principales de fuerza
			</p>
		</div>
		""", unsafe_allow_html=True)
		
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
			
			st.plotly_chart(fig_radar_simple, use_container_width=True, config=radar_config, height=600)
			
			# Información resumida debajo del radar
			if zscores_radar:
				st.markdown("### 📊 Resumen de Rendimiento")
				
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
			st.warning("⚠️ Datos insuficientes para Z-Scores. Se requieren al menos 3 jugadores en la categoría.")
			
			# Mostrar mensaje centrado
			col1, col_center, col2 = st.columns([1, 2, 1])
			with col_center:
				st.info("📊 Agregue más jugadores a la categoría para habilitar el análisis Z-Score.")
		


		# === TABLA COMPARATIVA ===
		st.markdown(f"#### Tabla - {jugador}")

		# Usar función optimizada con cache para procesar datos
		df_categoria = procesar_datos_categoria(df, categoria)
		
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

		# Usar funciones optimizadas con cache
		jugador_dict = preparar_datos_jugador(datos_jugador_dict, columnas_tabla)
		media_dict, std_dict = calcular_estadisticas_categoria(df_categoria, columnas_tabla)
		
		# Agregar métricas totales al diccionario del jugador
		for col_total in columnas_totales:
			if col_total in datos_jugador_dict:
				jugador_dict[col_total] = round(datos_jugador_dict.get(col_total, 0), 1)
				# Calcular estadísticas para métricas totales
				valores_totales = pd.to_numeric(df_categoria[col_total], errors="coerce").dropna()
				if len(valores_totales) > 0:
					media_dict[col_total] = round(valores_totales.mean(), 1)
					std_dict[col_total] = round(valores_totales.std(), 1)
				else:
					media_dict[col_total] = 0.0
					std_dict[col_total] = 0.0

		# Ordenar columnas como pares + totales
		column_order = []
		for der, izq in columnas_tabla.items():
			column_order.extend([der, izq])
		column_order.extend(columnas_totales)

		# Crear DataFrame comparativo original
		df_comparativo = pd.DataFrame([
			jugador_dict,
			media_dict,
			std_dict
		])[column_order]
		df_comparativo.index = [f"{jugador}", f"Media {categoria}", f"Desv. Est. {categoria}"]
		
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
