"""
Módulo de análisis de movilidad
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from visualizations.charts import (
	crear_grafico_multimovilidad,
	crear_radar_zscore_simple_movilidad,
	crear_grafico_multimovilidad_comparativo,
	crear_radar_zscore_comparativo,
	crear_grafico_multimovilidad_grupal,
)
from utils.data_utils import (
	procesar_datos_categoria, calcular_estadisticas_categoria, preparar_datos_jugador,
	calcular_zscores_automaticos, generar_zscores_jugador, calcular_zscores_radar_simple, generar_zscores_radar_simple,
	calcular_estadisticas_completas_categoria, preparar_datos_jugador_completo, calcular_estadisticas_distribucion_grupal
)
from config.settings import PLOTLY_CONFIG, METRICAS_ZSCORE_MOVILIDAD, COLORES, ESCUDO_PATH


def obtener_componentes_perfil_movilidad(df, datos_jugador, jugador, categoria, metricas_seleccionadas=None):
	"""Obtiene figuras y tablas del perfil de movilidad SIN usar Streamlit.

	Devuelve los mismos elementos conceptuales que se muestran en `analizar_movilidad`:
	- Gráfico multimovilidad
	- Radar Z-Score simplificado de movilidad
	- Tabla resumen de Z-Scores de movilidad
	- Tabla comparativa jugador vs grupo (movilidad)

	Parameters
	----------
	df : pd.DataFrame
		DataFrame completo con todos los jugadores.
	datos_jugador : pd.Series o dict
		Fila correspondiente al jugador seleccionado.
	jugador : str
		Nombre del jugador.
	categoria : str
		Categoría del jugador.
	metricas_seleccionadas : list[str] | None
		Lista de métricas de movilidad seleccionadas ("AKE", "THOMAS", "LUNGE"). Si es None se usan las
		mismas por defecto que en la vista de Streamlit.

	Returns
	-------
	dict
		{
			"figuras": [fig_multimovilidad, fig_radar_simple],
			"tablas": {
				"zscores": df_zscores,
				"comparativa": df_transpuesto
			}
		}
	"""

	# === Configuración de métricas (igual que en analizar_movilidad) ===
	metricas_disponibles = ["AKE", "THOMAS", "LUNGE"]
	metricas_columnas = {
		"AKE": ("AKE DER", "AKE IZQ"),
		"THOMAS": ("THOMAS DER", "THOMAS IZQ"),
		"LUNGE": ("LUNGE DER", "LUNGE IZQ"),
	}

	if metricas_seleccionadas is None:
		metricas_seleccionadas = ["AKE", "THOMAS", "LUNGE"]

	# === FIGURA: Gráfico multimovilidad ===
	datos_jugador_dict = datos_jugador.to_dict() if hasattr(datos_jugador, "to_dict") else dict(datos_jugador)
	fig_multimovilidad = crear_grafico_multimovilidad(
		datos_jugador_dict,
		tuple(metricas_seleccionadas),
		metricas_columnas,
	)

	# === RADAR Z-SCORE SIMPLIFICADO MOVILIDAD ===
	df_categoria = procesar_datos_categoria(df, categoria)
	estadisticas_radar = calcular_zscores_radar_simple(df_categoria, METRICAS_ZSCORE_MOVILIDAD)
	fig_radar_simple = None
	df_zscores = pd.DataFrame()

	if estadisticas_radar:
		zscores_radar = generar_zscores_radar_simple(
			datos_jugador,
			estadisticas_radar,
			METRICAS_ZSCORE_MOVILIDAD,
		)

		# Crear figura de radar de movilidad
		fig_radar_simple = crear_radar_zscore_simple_movilidad(zscores_radar, jugador)

		# Construir tabla resumen de Z-Scores de movilidad
		filas = []
		for metrica, data in zscores_radar.items():
			zscore = data["zscore"]
			valor = data["valor_original"]

			if zscore >= 1.0:
				categoria_nivel = "Superior"
			elif zscore >= 0.0:
				categoria_nivel = "Promedio+"
			elif zscore >= -1.0:
				categoria_nivel = "Promedio-"
			else:
				categoria_nivel = "Inferior"

			filas.append(
				{
					"Métrica": metrica,
					"Z-Score": zscore,
					"Valor": valor,
					"Categoría": categoria_nivel,
				}
			)

		if filas:
			df_zscores = pd.DataFrame(filas).set_index("Métrica")

	# === TABLA COMPARATIVA JUGADOR VS GRUPO (MOVILIDAD) ===
	columnas_tabla = {
		"AKE DER": "AKE IZQ",
		"THOMAS DER": "THOMAS IZQ",
		"LUNGE DER": "LUNGE IZQ",
	}
	columnas_totales = []  # No hay totales en movilidad

	categorias_disponibles = df["categoria"].value_counts()
	categoria_base = categorias_disponibles.index[0]
	df_categoria_base = procesar_datos_categoria(df, categoria_base)
	estadisticas_grupales = calcular_estadisticas_completas_categoria(
		df_categoria_base,
		columnas_tabla,
		columnas_totales,
	)

	jugador_dict = preparar_datos_jugador_completo(
		datos_jugador_dict,
		columnas_tabla,
		columnas_totales,
	)

	column_order = []
	for der, izq in columnas_tabla.items():
		column_order.extend([der, izq])

	columnas_validas = []
	for col in column_order:
		if (
			col in jugador_dict
			and col in estadisticas_grupales["media"]
			and col in estadisticas_grupales["std"]
		):
			columnas_validas.append(col)

	if columnas_validas:
		df_comparativo = pd.DataFrame(
			[
				jugador_dict,
				estadisticas_grupales["media"],
				estadisticas_grupales["std"],
			]
		)[columnas_validas]
		
		df_comparativo.index = [f"{jugador}", "Media", "Desviación Estándar"]
		df_transpuesto = df_comparativo.T
		df_transpuesto.index.name = "Métrica"
	else:
		df_transpuesto = pd.DataFrame()

	figuras = [fig_multimovilidad]
	if fig_radar_simple is not None:
		figuras.append(fig_radar_simple)

	return {
		"figuras": figuras,
		"tablas": {
			"zscores": df_zscores,
			"comparativa": df_transpuesto,
		},
	}


def obtener_componentes_perfil_movilidad_grupal(df, categoria, metricas_seleccionadas=None):
	"""Obtiene figuras y tabla del perfil de movilidad GRUPAL SIN usar Streamlit.

	Reproduce los elementos clave de `analizar_movilidad_grupal`:
	- Gráfico multimovilidad grupal (medias bilaterales)
	- Tabla grupal (media y desviación estándar por métrica)
	"""

	# Configuración de métricas igual que en analizar_movilidad_grupal
	metricas_disponibles = ["AKE", "THOMAS", "LUNGE"]
	metricas_display = ["AKE", "THOMAS", "LUNGE"]
	metricas_columnas = {
		"AKE": ("AKE DER", "AKE IZQ"),
		"THOMAS": ("THOMAS DER", "THOMAS IZQ"),
		"LUNGE": ("LUNGE DER", "LUNGE IZQ"),
	}

	if metricas_seleccionadas is None:
		metricas_seleccionadas = ["AKE", "THOMAS", "LUNGE"]

	# Procesar datos de la categoría
	df_categoria = procesar_datos_categoria(df, categoria)

	# Calcular estadísticas grupales para las métricas seleccionadas
	estadisticas_grupales = {}
	for metrica in metricas_seleccionadas:
		col_der, col_izq = metricas_columnas[metrica]

		valores_der = pd.to_numeric(df_categoria.get(col_der, []), errors="coerce").dropna()
		valores_izq = pd.to_numeric(df_categoria.get(col_izq, []), errors="coerce").dropna()

		if len(valores_der) > 0 and len(valores_izq) > 0:
			estadisticas_grupales[metrica] = {
				"media_der": round(valores_der.mean(), 1),
				"media_izq": round(valores_izq.mean(), 1),
				"std_der": round(valores_der.std(), 1) if len(valores_der) > 1 else 0.0,
				"std_izq": round(valores_izq.std(), 1) if len(valores_izq) > 1 else 0.0,
				"n_jugadores": min(len(valores_der), len(valores_izq)),
			}

	# Gráfico de barras grupal de movilidad
	fig_multimovilidad_grupal = crear_grafico_multimovilidad_grupal(
		estadisticas_grupales,
		tuple(metricas_seleccionadas),
		categoria,
	)

	# ===== Gráfico de DISTRIBUCIÓN GRUPAL de movilidad (similar a analizar_movilidad_grupal) =====
	estadisticas_radar_grupal = {}
	metricas_movilidad = {
		"AKE": ("AKE DER", "AKE IZQ"),
		"THOMAS": ("THOMAS DER", "THOMAS IZQ"),
		"LUNGE": ("LUNGE DER", "LUNGE IZQ"),
	}
	for metrica, (col_der, col_izq) in metricas_movilidad.items():
		if col_der in df_categoria.columns and col_izq in df_categoria.columns:
			valores_der = pd.to_numeric(df_categoria[col_der], errors="coerce").dropna()
			valores_izq = pd.to_numeric(df_categoria[col_izq], errors="coerce").dropna()
			if len(valores_der) > 0 and len(valores_izq) > 0:
				promedios = []
				for i in range(min(len(valores_der), len(valores_izq))):
					if pd.notna(valores_der.iloc[i]) and pd.notna(valores_izq.iloc[i]):
						promedio = (valores_der.iloc[i] + valores_izq.iloc[i]) / 2
						promedios.append(promedio)
				if promedios:
					serie_prom = pd.Series(promedios)
					estadisticas_radar_grupal[f"{metrica}_PROMEDIO"] = {
						"media": serie_prom.mean(),
						"std": serie_prom.std() if len(serie_prom) > 1 else 0,
						"minimo": serie_prom.min(),
						"maximo": serie_prom.max(),
						"n": len(serie_prom),
						"label": metrica,
					}

	fig_distribucion_grupal = None
	if estadisticas_radar_grupal:
		metricas = []
		medias = []
		orden_metricas = ["AKE", "THOMAS", "LUNGE"]
		for metrica in orden_metricas:
			for _, stats in estadisticas_radar_grupal.items():
				if stats["label"] == metrica:
					metricas.append(metrica)
					medias.append(stats["media"])
					break
		fig_distribucion_grupal = go.Figure()
		fig_distribucion_grupal.add_trace(
			go.Bar(
				x=metricas,
				y=medias,
				name="Media del Grupo",
				marker=dict(
					color="rgba(220, 38, 38, 0.8)",
					line=dict(color="rgba(220, 38, 38, 1)", width=2),
				),
				text=[f"{v:.0f}°" for v in medias],
				textposition="outside",
				textfont=dict(size=14, color="white", family="Roboto", weight="bold"),
				hovertemplate="<b>%{x}</b><br>Media: %{y:.1f}°<extra></extra>",
				hoverlabel=dict(
					bgcolor="rgba(220, 38, 38, 0.9)",
					bordercolor="rgba(220, 38, 38, 1)",
					font=dict(color="white", family="Roboto"),
				),
			)
		)
		# Marca de agua del escudo
		try:
			from utils.ui_utils import get_base64_image
			escudo_base64 = get_base64_image(ESCUDO_PATH)
			fig_distribucion_grupal.add_layout_image(
				{
					"source": f"data:image/png;base64,{escudo_base64}",
					"xref": "paper",
					"yref": "paper",
					"x": 0.95,
					"y": 0.05,
					"sizex": 0.15,
					"sizey": 0.15,
					"xanchor": "right",
					"yanchor": "bottom",
					"opacity": 0.1,
					"layer": "below",
				},
			)
		except Exception:
			pass
		fig_distribucion_grupal.update_layout(
			title=dict(
				text=f"Distribución Grupal – {categoria}<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Movilidad – Medias del Grupo</span>",
				font=dict(size=18, family="Source Sans Pro", weight=600, color="rgba(220, 38, 38, 1)"),
				y=0.94,
				x=0.5,
				xanchor="center",
			),
			xaxis=dict(
				title=dict(text="Métrica", font=dict(size=14, family="Roboto"), standoff=20),
				tickfont=dict(size=12, family="Roboto"),
				showgrid=True,
				gridwidth=1,
				gridcolor="rgba(255,255,255,0.1)",
				tickangle=0,
				categoryorder="array",
				categoryarray=metricas,
			),
			yaxis=dict(
				title=dict(text="Movilidad (°)", font=dict(size=14, family="Roboto"), standoff=15),
				tickfont=dict(size=12, family="Roboto"),
				showgrid=True,
				gridwidth=1,
				gridcolor="rgba(255,255,255,0.1)",
				zeroline=True,
				zerolinewidth=2,
				zerolinecolor="rgba(255,255,255,0.3)",
			),
			legend=dict(
				orientation="h",
				yanchor="bottom",
				y=1.02,
				xanchor="center",
				x=0.5,
				font=dict(size=12, family="Roboto"),
				bgcolor="rgba(220, 38, 38, 0.2)",
				bordercolor="rgba(220, 38, 38, 0.5)",
				borderwidth=2,
			),
			plot_bgcolor=COLORES["fondo_oscuro"],
			paper_bgcolor=COLORES["fondo_oscuro"],
			font=dict(color="white", family="Roboto"),
			height=600,
			margin=dict(t=140, b=60, l=60, r=60),
			showlegend=True,
		)

	# Tabla comparativa grupal (media y desviación estándar)
	columnas_tabla = {
		"AKE DER": "AKE IZQ",
		"THOMAS DER": "THOMAS IZQ",
		"LUNGE DER": "LUNGE IZQ",
	}
	columnas_totales = []  # No hay totales en movilidad

	estadisticas_grupales_tabla = calcular_estadisticas_completas_categoria(
		df_categoria,
		columnas_tabla,
		columnas_totales,
	)

	column_order = []
	for der, izq in columnas_tabla.items():
		column_order.extend([der, izq])

	columnas_validas = []
	for col in column_order:
		if (
			col in estadisticas_grupales_tabla["media"]
			and col in estadisticas_grupales_tabla["std"]
		):
			columnas_validas.append(col)

	if columnas_validas:
		df_comparativo_grupal = pd.DataFrame(
			[
				estadisticas_grupales_tabla["media"],
				estadisticas_grupales_tabla["std"],
			]
		)[columnas_validas]
		
		df_comparativo_grupal.index = ["Media Grupal", "Desviación Estándar"]
		df_transpuesto_grupal = df_comparativo_grupal.T
		df_transpuesto_grupal.index.name = "Métrica"
	else:
		df_transpuesto_grupal = pd.DataFrame()

	figuras = [fig_multimovilidad_grupal]
	if fig_distribucion_grupal is not None:
		figuras.append(fig_distribucion_grupal)

	return {
		"figuras": figuras,
		"tablas": {
			"comparativa_grupal": df_transpuesto_grupal,
		},
	}

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

def analizar_movilidad_grupal(df, categoria):
	"""Realiza el análisis completo de movilidad GRUPAL - métricas agregadas"""
	
	# Mapeo de nombres técnicos a nombres amigables
	mapeo_categorias = {
		"Evaluacion_2910": "Primer Equipo",
		"Reserva": "Reserva",
		"4ta": "4ta División"
	}
	categoria_display = mapeo_categorias.get(categoria, categoria)
	
	# === Selección de métricas de movilidad - IGUAL QUE INDIVIDUAL ===
	metricas_disponibles = ["AKE", "THOMAS", "LUNGE"]
	metricas_display = ["AKE", "THOMAS", "LUNGE"]
	metricas_columnas = {
		"AKE": ("AKE DER", "AKE IZQ"),
		"THOMAS": ("THOMAS DER", "THOMAS IZQ"),
		"LUNGE": ("LUNGE DER", "LUNGE IZQ")
	}

	metricas_seleccionadas_display = st.multiselect(
		"Selección de Métricas - Selecciona las evaluaciones para el análisis grupal:",
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
		
		# Procesar datos de la categoría para obtener estadísticas grupales
		df_categoria = procesar_datos_categoria(df, categoria)
		
		# Calcular estadísticas grupales para las métricas seleccionadas
		estadisticas_grupales = {}
		for metrica in metricas_seleccionadas:
			col_der, col_izq = metricas_columnas[metrica]
			
			# Para métricas bilaterales de movilidad, calcular medias de cada lado
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
		from visualizations.charts import crear_grafico_multimovilidad_grupal
		fig_multimovilidad_grupal = crear_grafico_multimovilidad_grupal(estadisticas_grupales, tuple(metricas_seleccionadas), categoria_display)
		
		# Mostrar gráfico con animación
		st.markdown("""
		<div style="animation: fadeInUp 0.8s ease-out;">
		""", unsafe_allow_html=True)
		
		st.plotly_chart(fig_multimovilidad_grupal, use_container_width=True, config=PLOTLY_CONFIG)
		
		st.markdown("</div>", unsafe_allow_html=True)
		
		# === DISTRIBUCIÓN GRUPAL ===
		st.markdown("<br><br>", unsafe_allow_html=True)
		
		# Header para la distribución grupal - EXACTAMENTE IGUAL AL DE FUERZA
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
		
		# Calcular estadísticas poblacionales para distribución grupal DE MOVILIDAD
		with st.spinner("Calculando distribución grupal..."):
			# Calcular estadísticas directamente para movilidad
			estadisticas_radar_grupal = {}
			
			# Definir las métricas de movilidad bilaterales
			metricas_movilidad = {
				'AKE': ('AKE DER', 'AKE IZQ'),
				'THOMAS': ('THOMAS DER', 'THOMAS IZQ'),
				'LUNGE': ('LUNGE DER', 'LUNGE IZQ')
			}
			
			for metrica, (col_der, col_izq) in metricas_movilidad.items():
				if col_der in df_categoria.columns and col_izq in df_categoria.columns:
					# Calcular promedios bilaterales
					valores_der = pd.to_numeric(df_categoria[col_der], errors='coerce').dropna()
					valores_izq = pd.to_numeric(df_categoria[col_izq], errors='coerce').dropna()
					
					if len(valores_der) > 0 and len(valores_izq) > 0:
						# Calcular promedio bilateral para cada jugador
						promedios = []
						for i in range(min(len(valores_der), len(valores_izq))):
							if pd.notna(valores_der.iloc[i]) and pd.notna(valores_izq.iloc[i]):
								promedio = (valores_der.iloc[i] + valores_izq.iloc[i]) / 2
								promedios.append(promedio)
						
						if promedios:
							promedios = pd.Series(promedios)
							estadisticas_radar_grupal[f'{metrica}_PROMEDIO'] = {
								'media': promedios.mean(),
								'std': promedios.std() if len(promedios) > 1 else 0,
								'minimo': promedios.min(),
								'maximo': promedios.max(),
								'n': len(promedios),
								'label': metrica
							}
				else:
					st.warning(f"⚠️ Columnas de movilidad no encontradas: {col_der}, {col_izq}")
		
		# Generar gráfico de distribución grupal (reemplaza al radar)
		if estadisticas_radar_grupal:
			# Crear gráfico de distribución específico para MOVILIDAD
			import plotly.graph_objects as go
			from utils.ui_utils import get_base64_image
			from config.settings import COLORES, ESCUDO_PATH
			
			# Extraer datos para el gráfico de MOVILIDAD
			metricas = []
			medias = []
			minimos = []
			maximos = []
			
			# Orden específico para MOVILIDAD
			orden_metricas = ['AKE', 'THOMAS', 'LUNGE']
			
			for metrica in orden_metricas:
				for metrica_key, stats in estadisticas_radar_grupal.items():
					if stats['label'] == metrica:
						metricas.append(metrica)
						medias.append(stats['media'])
						minimos.append(stats['minimo'])
						maximos.append(stats['maximo'])
						break
			
			# Crear el gráfico de barras con rangos para MOVILIDAD
			fig_distribucion_grupal = go.Figure()
			
			# Barras principales (medias del grupo)
			fig_distribucion_grupal.add_trace(go.Bar(
				x=metricas,
				y=medias,
				name="Media del Grupo",
				marker=dict(
					color="rgba(220, 38, 38, 0.8)",
					line=dict(color="rgba(220, 38, 38, 1)", width=2)
				),
				text=[f"{v:.0f}°" for v in medias],
				textposition="outside",
				textfont=dict(size=14, color="white", family="Roboto", weight="bold"),
				hovertemplate='<b>%{x}</b><br>' +
							  'Media: %{y:.1f}°<br>' +
							  '<extra></extra>',
				hoverlabel=dict(
					bgcolor="rgba(220, 38, 38, 0.9)",
					bordercolor="rgba(220, 38, 38, 1)",
					font=dict(color="white", family="Roboto")
				)
			))
			
			# Agregar logo del club como marca de agua
			try:
				escudo_base64 = get_base64_image(ESCUDO_PATH)
				fig_distribucion_grupal.add_layout_image(
					dict(
						source=f"data:image/png;base64,{escudo_base64}",
						xref="paper", yref="paper",
						x=0.95, y=0.05,
						sizex=0.15, sizey=0.15,
						xanchor="right", yanchor="bottom",
						opacity=0.1,
						layer="below"
					)
				)
			except:
				pass

			fig_distribucion_grupal.update_layout(
				title=dict(
					text=f"Distribución Grupal – {categoria_display}<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Movilidad – Medias del Grupo</span>",
					font=dict(size=18, family="Source Sans Pro", weight=600, color="rgba(220, 38, 38, 1)"),
					y=0.94,
					x=0.5,
					xanchor="center"
				),
				xaxis=dict(
					title=dict(
						text="Métrica", 
						font=dict(size=14, family="Roboto"),
						standoff=20
					),
					tickfont=dict(size=12, family="Roboto"),
					showgrid=True,
					gridwidth=1,
					gridcolor="rgba(255,255,255,0.1)",
					tickangle=0,
					categoryorder="array",
					categoryarray=metricas
				),
				yaxis=dict(
					title=dict(
						text="Movilidad (°)", 
						font=dict(size=14, family="Roboto"),
						standoff=15
					),
					tickfont=dict(size=12, family="Roboto"),
					showgrid=True,
					gridwidth=1,
					gridcolor="rgba(255,255,255,0.1)",
					zeroline=True,
					zerolinewidth=2,
					zerolinecolor="rgba(255,255,255,0.3)"
				),
				legend=dict(
					orientation="h",
					yanchor="bottom",
					y=1.02,
					xanchor="center",
					x=0.5,
					font=dict(size=12, family="Roboto"),
					bgcolor="rgba(220, 38, 38, 0.2)",
					bordercolor="rgba(220, 38, 38, 0.5)",
					borderwidth=2
				),
				plot_bgcolor=COLORES['fondo_oscuro'],
				paper_bgcolor=COLORES['fondo_oscuro'],
				font=dict(color="white", family="Roboto"),
				height=600,
				margin=dict(t=140, b=60, l=60, r=60),
				showlegend=True,
				transition=dict(
					duration=800,
					easing="cubic-in-out"
				),
				hovermode="x unified",
				hoverdistance=100,
				spikedistance=1000
			)
			
			distribucion_config = PLOTLY_CONFIG.copy()
			distribucion_config['toImageButtonOptions'].update({
				'filename': f'distribucion_grupal_movilidad_{categoria}',
				'height': 600,
				'width': 800
			})
			
			st.plotly_chart(fig_distribucion_grupal, use_container_width=True, config=distribucion_config)
			
			# Información resumida debajo del gráfico de distribución
			if estadisticas_radar_grupal:
				# Crear métricas en columnas
				metricas_info = []
				orden_metricas = ['AKE', 'THOMAS', 'LUNGE']
				
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
									{media:.0f}°
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

		# Columnas de movilidad que queremos analizar - IGUAL QUE INDIVIDUAL
		columnas_tabla = {
			"AKE DER": "AKE IZQ",
			"THOMAS DER": "THOMAS IZQ",
			"LUNGE DER": "LUNGE IZQ"
		}
		
		# No hay métricas totales en movilidad
		columnas_totales = []

		# CALCULAR ESTADÍSTICAS GRUPALES PARA LA CATEGORÍA SELECCIONADA
		estadisticas_grupales_tabla = calcular_estadisticas_completas_categoria(df_categoria, columnas_tabla, columnas_totales)
		
		# Obtener número de jugadores para los nombres de las filas
		n_jugadores_categoria = estadisticas_grupales_tabla['n_jugadores']

		# Ordenar columnas como pares
		column_order = []
		for der, izq in columnas_tabla.items():
			column_order.extend([der, izq])

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


def analizar_movilidad_comparativo(df, datos_jugador, jugador, categoria):
	"""Realiza el análisis COMPARATIVO de movilidad (Jugador vs Grupo)"""

	# === Selección de métricas de movilidad ===
	metricas_disponibles = ["AKE", "THOMAS", "LUNGE"]
	metricas_display = ["AKE", "THOMAS", "LUNGE"]
	metricas_columnas = {
		"AKE": ("AKE DER", "AKE IZQ"),
		"THOMAS": ("THOMAS DER", "THOMAS IZQ"),
		"LUNGE": ("LUNGE DER", "LUNGE IZQ"),
	}

	metricas_seleccionadas_display = st.multiselect(
		"Selección de Métricas - Selecciona las evaluaciones para la comparación:",
		metricas_disponibles,
		default=["AKE", "THOMAS", "LUNGE"],
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

		# === GRÁFICO DE BARRAS COMPARATIVO ===
		# Optimización con cache - crear hash del jugador
		datos_jugador_dict = datos_jugador.to_dict() if hasattr(datos_jugador, "to_dict") else dict(datos_jugador)

		# Calcular estadísticas grupales para comparación (misma categoría seleccionada)
		with st.spinner("Calculando estadísticas grupales para comparación de movilidad..."):
			df_categoria = procesar_datos_categoria(df, categoria)

			# Formato esperado por calcular_estadisticas_completas_categoria: {"AKE DER": "AKE IZQ", ...}
			columnas_tabla = {}
			for metrica, (col_der, col_izq) in metricas_columnas.items():
				columnas_tabla[col_der] = col_izq

			# En movilidad no hay métricas totales
			columnas_totales = []
			estadisticas_grupales = calcular_estadisticas_completas_categoria(
				df_categoria,
				columnas_tabla,
				columnas_totales,
			)

		# Generar gráfico comparativo con cache optimizado
		fig_multimovilidad_comparativo = crear_grafico_multimovilidad_comparativo(
			datos_jugador_dict,
			estadisticas_grupales,
			tuple(metricas_seleccionadas),
			metricas_columnas,
			jugador,
		)

		# Mostrar gráfico con animación
		st.markdown(
			"""
		<div style="animation: fadeInUp 0.8s ease-out;">
		""",
			unsafe_allow_html=True,
		)

		st.plotly_chart(
			fig_multimovilidad_comparativo,
			use_container_width=True,
			config=PLOTLY_CONFIG,
		)

		st.markdown("</div>", unsafe_allow_html=True)

		# === RADAR Z-SCORE COMPARATIVO ===
		st.markdown("<br><br>", unsafe_allow_html=True)

		# Header para el radar comparativo (idéntico al de fuerza)
		st.markdown(
			f"""
		<div style='background: linear-gradient(90deg, rgba(220, 38, 38, 0.8), rgba(17, 24, 39, 0.8));
					border-left: 4px solid rgba(220, 38, 38, 1); padding: 15px; border-radius: 8px;'>
			<h4 style='margin: 0; color: white; font-family: "Source Sans Pro", sans-serif; font-weight: 600; font-size: 1.5rem; line-height: 1.2; padding: 0.75rem 0 1rem;'>
				Radar Comparativo Z-Score
			</h4>
		</div>
		""",
			unsafe_allow_html=True,
		)

		# Espaciado para mejorar el estilo visual
		st.markdown("<br>", unsafe_allow_html=True)

		# Calcular estadísticas poblacionales para radar de MOVILIDAD
		with st.spinner("Calculando estadísticas para radar de movilidad..."):
			df_categoria = procesar_datos_categoria(df, categoria)
			estadisticas_radar = calcular_zscores_radar_simple(
				df_categoria, METRICAS_ZSCORE_MOVILIDAD
			)

		# Generar Z-Scores simplificados del jugador (MISMO RADAR QUE EN PERFIL DEL JUGADOR)
		if estadisticas_radar:
			zscores_radar = generar_zscores_radar_simple(
				datos_jugador, estadisticas_radar, METRICAS_ZSCORE_MOVILIDAD
			)
			
			fig_radar_simple = crear_radar_zscore_simple_movilidad(zscores_radar, jugador)
			
			radar_config = PLOTLY_CONFIG.copy()
			radar_config["toImageButtonOptions"].update(
				{
					"filename": f"radar_simple_movilidad_comparativo_{jugador}_{categoria}",
					"height": 600,
					"width": 800,
				}
			)
			
			st.plotly_chart(fig_radar_simple, use_container_width=True, config=radar_config)
		else:
			st.warning(
				"Datos insuficientes para Z-Scores de movilidad en el radar. Se requieren al menos 3 jugadores en la categoría."
			)

		# === TABLA COMPARATIVA ===
		st.markdown("<br><br>", unsafe_allow_html=True)

		# Header para la tabla comparativa (idéntico al de fuerza)
		st.markdown(
			f"""
		<div style='background: linear-gradient(90deg, rgba(220, 38, 38, 0.8), rgba(17, 24, 39, 0.8));
					border-left: 4px solid rgba(220, 38, 38, 1); padding: 15px; border-radius: 8px;'>
				<h4 style='margin: 0; color: white; font-family: "Source Sans Pro", sans-serif; font-weight: 600; font-size: 1.5rem; line-height: 1.2; padding: 0.75rem 0 1rem;'>
					Tabla comparativa – {jugador} vs Grupo
				</h4>
			</div>
		""",
			unsafe_allow_html=True,
		)

		st.markdown("<br>", unsafe_allow_html=True)

		# Crear tabla comparativa de movilidad (solo métricas bilaterales)
		tabla_comparativa = {}

		for metrica in metricas_seleccionadas:
			col_der, col_izq = metricas_columnas[metrica]
			if (
				col_der in estadisticas_grupales["media"]
				and col_izq in estadisticas_grupales["media"]
			):
				val_der_jugador = datos_jugador.get(col_der, 0)
				val_izq_jugador = datos_jugador.get(col_izq, 0)
				promedio_jugador = (val_der_jugador + val_izq_jugador) / 2

				val_der_grupo = estadisticas_grupales["media"][col_der]
				val_izq_grupo = estadisticas_grupales["media"][col_izq]
				promedio_grupo = (val_der_grupo + val_izq_grupo) / 2

				diferencia = promedio_jugador - promedio_grupo
				porcentaje = (
					(promedio_jugador / promedio_grupo) * 100 - 100
					if promedio_grupo > 0
					else 0
				)

				tabla_comparativa[metrica] = {
					f"{jugador}": f"{promedio_jugador:.1f}°",
					"Media grupo": f"{promedio_grupo:.1f}°",
					"Diferencia": f"{diferencia:+.1f}°",
					"% vs Grupo": f"{porcentaje:+.1f}%",
				}

		# Convertir a DataFrame (mismas columnas que fuerza: jugador, grupo, diferencia, %)
		if tabla_comparativa:
			df_comparativo = pd.DataFrame(tabla_comparativa).T
		
			st.dataframe(
				df_comparativo.style.apply(
					lambda x: [
						"background-color: rgba(220, 38, 38, 0.15); font-weight: bold;",  # Columna jugador
						"background-color: rgba(59, 130, 246, 0.15);",                   # Columna grupo
						"background-color: rgba(31, 41, 55, 0.15);",                     # Diferencia
						"background-color: rgba(255, 193, 7, 0.15);",                    # % vs grupo
					],
					axis=1,
					).set_table_styles([
						{
							"selector": "th.col_heading",
							"props": "background-color: rgba(220, 38, 38, 0.3); color: white; font-weight: bold;",
						},
						{
							"selector": "th.row_heading",
							"props": "background-color: rgba(31, 41, 55, 0.8); color: white; font-weight: bold; text-align: left;",
						},
						{
							"selector": "td",
							"props": "text-align: center; padding: 8px;",
						},
					]),
				use_container_width=True,
			)
		else:
			st.info(
				"No se pudo generar la tabla comparativa de movilidad. Verificar datos disponibles."
			)
	else:
		st.info("Selecciona al menos una métrica para visualizar la comparación de movilidad.")
