"""
Módulo de visualizaciones - Gráficos y charts
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config.settings import CACHE_TTL, COLORES, Z_SCORE_METRICAS, METRICAS_ZSCORE_FUERZA, METRICAS_ZSCORE_RADAR_SIMPLE, METRICAS_ZSCORE_MOVILIDAD, ESCUDO_PATH
from utils.ui_utils import get_base64_image

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico de fuerza...")
def crear_grafico_multifuerza(datos_jugador_hash, metricas_seleccionadas, metricas_columnas):
	"""Crea gráfico de multifuerza con cache optimizado"""
	# Reconstruir datos del jugador desde hash
	datos_jugador = datos_jugador_hash
	
	# Separar métricas bilaterales y totales
	metricas_bilaterales = []
	metricas_totales = []
	barras_der, barras_izq, nombres_bilaterales = [], [], []
	valores_totales, nombres_totales = [], []
	lsi_labels = {}

	for metrica in metricas_seleccionadas:
		# Métricas totales (no bilaterales)
		if metrica in ["IMTP Total", "CMJ FP Total", "CMJ FF Total"]:
			col_total = metricas_columnas[metrica][0]  # Usar la primera columna (son iguales)
			val_total = datos_jugador.get(col_total, 0)
			valores_totales.append(val_total)
			nombres_totales.append(metrica)
			metricas_totales.append(metrica)
			
		# Métricas bilaterales tradicionales
		else:
			col_der, col_izq = metricas_columnas[metrica]
			val_der = datos_jugador.get(col_der, 0)
			val_izq = datos_jugador.get(col_izq, 0)
			barras_der.append(val_der)
			barras_izq.append(val_izq)
			nombres_bilaterales.append(metrica)
			metricas_bilaterales.append(metrica)
			
			# Calcular LSI para métricas bilaterales
			if val_der > 0 and val_izq > 0:
				lsi_val = (min(val_der, val_izq) / max(val_der, val_izq)) * 100
				lsi_labels[metrica] = lsi_val

	fig = go.Figure()

	# Agregar trazas para métricas bilaterales (si existen)
	if nombres_bilaterales:
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_der,
			name="🔴 Derecho",
			marker=dict(
				color=COLORES['rojo_colon'],
				pattern=dict(
					shape="",
					bgcolor="rgba(220, 38, 38, 0.3)",
					fgcolor="rgba(220, 38, 38, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in barras_der],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>🔴 Derecho</b><br>%{x}: %{y:.0f} N<br><i>Lado dominante</i><extra></extra>',
			offsetgroup=1,
			hoverlabel=dict(
				bgcolor="rgba(220, 38, 38, 0.9)",
				bordercolor="rgba(220, 38, 38, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_izq,
			name="⚫ Izquierdo",
			marker=dict(
				color=COLORES['negro_colon'],
				pattern=dict(
					shape="",
					bgcolor="rgba(31, 41, 55, 0.3)",
					fgcolor="rgba(31, 41, 55, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in barras_izq],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>⚫ Izquierdo</b><br>%{x}: %{y:.0f} N<br><i>Lado no dominante</i><extra></extra>',
			offsetgroup=2,
			hoverlabel=dict(
				bgcolor="rgba(31, 41, 55, 0.9)",
				bordercolor="rgba(31, 41, 55, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# Agregar traza para métricas totales (si existen) - UNA SOLA BARRA CENTRADA
	if nombres_totales:
		fig.add_trace(go.Bar(
			x=nombres_totales,
			y=valores_totales,
			name="🟡 Total",
			marker=dict(
				color="rgba(255, 193, 7, 0.9)",  # Color dorado para totales
				pattern=dict(
					shape="",
					bgcolor="rgba(255, 193, 7, 0.3)",
					fgcolor="rgba(255, 193, 7, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in valores_totales],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>🟡 Total</b><br>%{x}: %{y:.0f} N<br><i>Valor bilateral combinado</i><extra></extra>',
			offsetgroup=3,
			hoverlabel=dict(
				bgcolor="rgba(255, 193, 7, 0.9)",
				bordercolor="rgba(255, 193, 7, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# LSI annotations - SOLO PARA MÉTRICAS BILATERALES
	for i, name in enumerate(nombres_bilaterales):
		lsi_val = lsi_labels.get(name)
		
		if lsi_val and lsi_val > 0:
			# Determinar color según rango LSI
			if 90 <= lsi_val <= 110:  # Zona óptima
				lsi_color = COLORES['verde_optimo']
				border_color = "rgba(50, 205, 50, 1)"
			elif 80 <= lsi_val < 90 or 110 < lsi_val <= 120:  # Zona de alerta
				lsi_color = COLORES['naranja_alerta']
				border_color = "rgba(255, 165, 0, 1)"
			else:  # Zona de riesgo
				lsi_color = COLORES['rojo_riesgo']
				border_color = "rgba(255, 69, 0, 1)"
			
			fig.add_annotation(
				text=f"<b>LSI: {lsi_val:.1f}%</b>",
				x=name,
				y=max(barras_der[i], barras_izq[i]) * 1.55,
				showarrow=False,
				font=dict(size=11, color="white", family="Roboto", weight="bold"),
				xanchor="center",
				align="center",
				bgcolor=lsi_color,
				bordercolor=border_color,
				borderwidth=2,
				borderpad=8,
				opacity=0.95
			)
	
	# Agregar logo del club como marca de agua
	try:
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		fig.add_layout_image(
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

	fig.update_layout(
		barmode="group",
		bargap=0.3,
		bargroupgap=0.1,
		title=dict(
			text="Evaluación Física Integral – Atlético Colón<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Fuerza – Bilaterales y Totales</span>",
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
			categoryarray=nombres_bilaterales + nombres_totales
		),
		yaxis=dict(
			title=dict(
				text="Fuerza (N)", 
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
		height=650,
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

	return fig


@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico comparativo de movilidad...")
def crear_grafico_multimovilidad_comparativo(datos_jugador_hash, estadisticas_grupales, metricas_seleccionadas, metricas_columnas, jugador_nombre):
	"""Crea gráfico de multimovilidad COMPARATIVO (Jugador vs Grupo superpuesto)"""
	# Reconstruir datos del jugador desde hash
	datos_jugador = datos_jugador_hash

	# Datos del JUGADOR
	barras_der_jugador, barras_izq_jugador, nombres_bilaterales = [], [], []
	lsi_labels_jugador = {}

	# Datos del GRUPO
	barras_der_grupo, barras_izq_grupo = [], []

	for metrica in metricas_seleccionadas:
		col_der, col_izq = metricas_columnas[metrica]

		# JUGADOR
		val_der_jugador = datos_jugador.get(col_der, 0)
		val_izq_jugador = datos_jugador.get(col_izq, 0)
		barras_der_jugador.append(val_der_jugador)
		barras_izq_jugador.append(val_izq_jugador)
		nombres_bilaterales.append(metrica)

		# LSI del jugador
		if val_der_jugador > 0 and val_izq_jugador > 0:
			lsi_val_jugador = (min(val_der_jugador, val_izq_jugador) / max(val_der_jugador, val_izq_jugador)) * 100
			lsi_labels_jugador[metrica] = lsi_val_jugador

		# GRUPO
		if col_der in estadisticas_grupales['media'] and col_izq in estadisticas_grupales['media']:
			val_der_grupo = estadisticas_grupales['media'][col_der]
			val_izq_grupo = estadisticas_grupales['media'][col_izq]
			barras_der_grupo.append(val_der_grupo)
			barras_izq_grupo.append(val_izq_grupo)
		else:
			barras_der_grupo.append(0)
			barras_izq_grupo.append(0)

	fig = go.Figure()

	# === BARRAS DEL GRUPO (FONDO - SEMITRANSPARENTES) ===
	if nombres_bilaterales:
		# Grupo Derecho
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_der_grupo,
			name="🔵 Grupo Derecho",
			marker=dict(
				color="rgba(59, 130, 246, 0.4)",
				line=dict(color="rgba(59, 130, 246, 0.8)", width=1),
				opacity=0.6,
			),
			text=[f"{v:.0f}" for v in barras_der_grupo],
			textposition="outside",
			textfont=dict(size=11, color="rgba(59, 130, 246, 0.9)", family="Roboto"),
			hovertemplate='<b>🔵 Grupo Derecho</b><br>%{x}: %{y:.0f}°<br><i>Media grupal</i><extra></extra>',
			offsetgroup=1,
			hoverlabel=dict(
				bgcolor="rgba(59, 130, 246, 0.9)",
				bordercolor="rgba(59, 130, 246, 1)",
				font=dict(color="white", family="Roboto"),
			),
		))

		# Grupo Izquierdo
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_izq_grupo,
			name="🔵 Grupo Izquierdo",
			marker=dict(
				color="rgba(59, 130, 246, 0.3)",
				line=dict(color="rgba(59, 130, 246, 0.6)", width=1),
				opacity=0.5,
			),
			text=[f"{v:.0f}" for v in barras_izq_grupo],
			textposition="outside",
			textfont=dict(size=11, color="rgba(59, 130, 246, 0.8)", family="Roboto"),
			hovertemplate='<b>🔵 Grupo Izquierdo</b><br>%{x}: %{y:.0f}°<br><i>Media grupal</i><extra></extra>',
			offsetgroup=2,
			hoverlabel=dict(
				bgcolor="rgba(59, 130, 246, 0.9)",
				bordercolor="rgba(59, 130, 246, 1)",
				font=dict(color="white", family="Roboto"),
			),
		))

	# === BARRAS DEL JUGADOR (PRIMER PLANO - COLORES ORIGINALES) ===
	if nombres_bilaterales:
		# Jugador Derecho
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_der_jugador,
			name=f"🔴 {jugador_nombre} Derecho",
			marker=dict(
				color=COLORES['rojo_colon'],
				pattern=dict(
					shape="",
					bgcolor="rgba(220, 38, 38, 0.3)",
					fgcolor="rgba(220, 38, 38, 1)",
				),
				opacity=0.9,
			),
			text=[f"{v:.0f}°" for v in barras_der_jugador],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate=f'<b>🔴 {jugador_nombre} Derecho</b><br>%{{x}}: %{{y:.0f}}°<br><i>Jugador individual</i><extra></extra>',
			offsetgroup=3,
			hoverlabel=dict(
				bgcolor="rgba(220, 38, 38, 0.9)",
				bordercolor="rgba(220, 38, 38, 1)",
				font=dict(color="white", family="Roboto"),
			),
		))

		# Jugador Izquierdo
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_izq_jugador,
			name=f"⚫ {jugador_nombre} Izquierdo",
			marker=dict(
				color=COLORES['negro_colon'],
				pattern=dict(
					shape="",
					bgcolor="rgba(31, 41, 55, 0.3)",
					fgcolor="rgba(31, 41, 55, 1)",
				),
				opacity=0.9,
			),
			text=[f"{v:.0f}°" for v in barras_izq_jugador],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate=f'<b>⚫ {jugador_nombre} Izquierdo</b><br>%{{x}}: %{{y:.0f}}°<br><i>Jugador individual</i><extra></extra>',
			offsetgroup=4,
			hoverlabel=dict(
				bgcolor="rgba(31, 41, 55, 0.9)",
				bordercolor="rgba(31, 41, 55, 1)",
				font=dict(color="white", family="Roboto"),
			),
		))

	# === LSI ANNOTATIONS - SOLO PARA EL JUGADOR ===
	for i, name in enumerate(nombres_bilaterales):
		lsi_val_jugador = lsi_labels_jugador.get(name)

		if lsi_val_jugador and lsi_val_jugador > 0:
			# Determinar color según rango LSI
			if 90 <= lsi_val_jugador <= 110:
				lsi_color = COLORES['verde_optimo']
				border_color = "rgba(50, 205, 50, 1)"
			elif 80 <= lsi_val_jugador < 90 or 110 < lsi_val_jugador <= 120:
				lsi_color = COLORES['naranja_alerta']
				border_color = "rgba(255, 165, 0, 1)"
			else:
				lsi_color = COLORES['rojo_riesgo']
				border_color = "rgba(255, 69, 0, 1)"

			# Calcular altura máxima entre jugador y grupo
			max_altura = max(
				barras_der_jugador[i] if i < len(barras_der_jugador) else 0,
				barras_izq_jugador[i] if i < len(barras_izq_jugador) else 0,
				barras_der_grupo[i] if i < len(barras_der_grupo) else 0,
				barras_izq_grupo[i] if i < len(barras_izq_grupo) else 0,
			)

			fig.add_annotation(
				text=f"<b>LSI: {lsi_val_jugador:.1f}%</b>",
				x=name,
				y=max_altura * 1.65,
				showarrow=False,
				font=dict(size=11, color="white", family="Roboto", weight="bold"),
				xanchor="center",
				align="center",
				bgcolor=lsi_color,
				bordercolor=border_color,
				borderwidth=2,
				borderpad=8,
				opacity=0.95,
			)

	# Agregar logo del club como marca de agua
	try:
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		fig.add_layout_image(
			dict(
				source=f"data:image/png;base64,{escudo_base64}",
				xref="paper",
				yref="paper",
				x=0.95,
				y=0.05,
				sizex=0.15,
				sizey=0.15,
				xanchor="right",
				yanchor="bottom",
				opacity=0.1,
				layer="below",
			),
		)
	except:
		pass

	fig.update_layout(
		barmode="group",
		bargap=0.2,
		bargroupgap=0.05,
		title=dict(
			text=f"Comparación {jugador_nombre} vs Grupo<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Movilidad – Individual vs Media Grupal</span>",
			font=dict(size=18, family="Source Sans Pro", weight=600, color="rgba(220, 38, 38, 1)"),
			y=0.94,
			x=0.5,
			xanchor="center",
		),
		xaxis=dict(
			title=dict(
				text="Métrica",
				font=dict(size=14, family="Roboto"),
				standoff=20,
			),
			tickfont=dict(size=12, family="Roboto"),
			showgrid=True,
			gridwidth=1,
			gridcolor="rgba(255,255,255,0.1)",
			tickangle=0,
			categoryorder="array",
			categoryarray=nombres_bilaterales,
		),
		yaxis=dict(
			title=dict(
				text="Movilidad (°)",
				font=dict(size=14, family="Roboto"),
				standoff=15,
			),
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
			font=dict(size=11, family="Roboto"),
			bgcolor="rgba(220, 38, 38, 0.2)",
			bordercolor="rgba(220, 38, 38, 0.5)",
			borderwidth=2,
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Roboto"),
		height=700,
		margin=dict(t=140, b=60, l=60, r=60),
		showlegend=True,
		transition=dict(
			duration=800,
			easing="cubic-in-out",
		),
		hovermode="x unified",
		hoverdistance=100,
		spikedistance=1000,
	)

	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando radar Z-Score...")
def crear_radar_zscore_automatico(zscores_jugador, jugador_nombre):
	"""
	Crea un radar chart con Z-Scores calculados automáticamente
	
	Args:
		zscores_jugador: Dict con Z-Scores calculados por generar_zscores_jugador()
		jugador_nombre: Nombre del jugador
		
	Returns:
		Figura de Plotly con radar chart
	"""
	if not zscores_jugador:
		# Crear gráfico vacío si no hay datos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin datos suficientes para Z-Scores</b><br>Se requieren al menos 3 jugadores<br>en la categoría para calcular estadísticas",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=14, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=400
		)
		return fig
	
	# Extraer valores y etiquetas de los Z-Scores calculados
	valores = []
	etiquetas = []
	colores_puntos = []
	interpretaciones = []
	
	for metrica_label, data in zscores_jugador.items():
		if data['zscore'] is not None:
			valores.append(data['zscore'])
			etiquetas.append(metrica_label)
			colores_puntos.append(data['interpretacion']['color'])
			interpretaciones.append(data['interpretacion']['interpretacion'])
	
	if not valores:
		# Sin valores válidos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin Z-Scores válidos</b><br>Verificar datos del jugador",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=14, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=400
		)
		return fig
	
	# Crear el radar chart
	fig = go.Figure()
	
	# Agregar trace principal
	fig.add_trace(go.Scatterpolar(
		r=valores,
		theta=etiquetas,
		fill='toself',
		name=jugador_nombre,
		line=dict(color=COLORES['rojo_colon'], width=3),
		fillcolor="rgba(220, 38, 38, 0.25)",
		marker=dict(
			size=10,
			color=colores_puntos,
			line=dict(width=2, color="white"),
			opacity=0.9
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  'Z-Score: %{r:.2f}<br>' +
					  '<i>%{text}</i><extra></extra>',
		text=interpretaciones
	))
	
	# Agregar líneas de referencia
	fig.add_shape(
		type="circle",
		x0=-1, y0=-1, x1=1, y1=1,
		line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dash"),
		layer="below"
	)
	fig.add_shape(
		type="circle", 
		x0=-2, y0=-2, x1=2, y1=2,
		line=dict(color="rgba(255,255,255,0.2)", width=1, dash="dot"),
		layer="below"
	)
	
	# Leyenda interpretativa mejorada
	fig.add_annotation(
		text="<b>🎯 Interpretación Z-Score</b><br>" +
			 "<span style='color: #22c55e;'>▲ Z ≥ +1.0:</span> Superior (>84%)<br>" +
			 "<span style='color: #fbbf24;'>● Z = 0.0:</span> Promedio (50%)<br>" +
			 "<span style='color: #ef4444;'>▼ Z ≤ -1.0:</span> Inferior (<16%)<br>" +
			 "<span style='color: #dc2626;'>⚠ Z ≤ -2.0:</span> Crítico (<2.5%)",
		x=0.02,
		y=0.98,
		xref="paper",
		yref="paper",
		xanchor="left",
		yanchor="top",
		showarrow=False,
		font=dict(size=10, color="white", family="Roboto"),
		align="left",
		bgcolor="rgba(31, 41, 55, 0.95)",
		bordercolor="rgba(59, 130, 246, 0.8)",
		borderwidth=2,
		borderpad=8,
		opacity=0.95
	)
	
	# Estadísticas de la población
	n_poblacion = list(zscores_jugador.values())[0]['n_poblacion'] if zscores_jugador else 0
	fig.add_annotation(
		text=f"<b>📊 Referencia Poblacional</b><br>N = {n_poblacion} jugadores<br>Categoría actual",
		x=0.98,
		y=0.02,
		xref="paper",
		yref="paper", 
		xanchor="right",
		yanchor="bottom",
		showarrow=False,
		font=dict(size=9, color="white", family="Roboto"),
		align="right",
		bgcolor="rgba(31, 41, 55, 0.9)",
		bordercolor="rgba(220, 38, 38, 0.6)",
		borderwidth=1,
		borderpad=6,
		opacity=0.9
	)
	
	fig.update_layout(
		polar=dict(
			radialaxis=dict(
				visible=True,
				range=[-3, 3],
				tickvals=[-2, -1, 0, 1, 2],
				ticktext=['-2σ', '-1σ', 'μ', '+1σ', '+2σ'],
				tickfont=dict(size=10, color="white"),
				gridcolor="rgba(255,255,255,0.3)",
				linecolor="rgba(255,255,255,0.5)"
			),
			angularaxis=dict(
				tickfont=dict(size=11, color="white", family="Roboto"),
				linecolor="rgba(255,255,255,0.5)",
				gridcolor="rgba(255,255,255,0.2)"
			),
			bgcolor=COLORES['fondo_oscuro']
		),
		showlegend=False,
		title=dict(
			text=f"⚽ Perfil Z-Score - {jugador_nombre} ⚽<br><span style='font-size:12px; color:rgba(255,255,255,0.7);'>Comparación vs Grupo de Referencia</span>",
			font=dict(size=16, color="rgba(220, 38, 38, 1)", family="Roboto", weight="bold"),
			x=0.5,
			xanchor="center",
			y=0.95
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Roboto"),
		height=550,
		margin=dict(t=80, b=60, l=60, r=60)
	)
	
	return fig

# Mantener función legacy para compatibilidad
@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando radar Z-Score...")
def crear_radar_zscore(datos_jugador_hash, jugador_nombre):
	"""Función legacy - mantener para compatibilidad con Z-Scores existentes en Excel"""
	# Reconstruir datos del jugador desde hash
	datos_jugador = datos_jugador_hash
	
	# Definir las métricas Z-Score y sus etiquetas
	z_score_metricas = Z_SCORE_METRICAS
	
	# Extraer valores y etiquetas
	valores = []
	etiquetas = []
	
	for columna, etiqueta in z_score_metricas.items():
		if columna in datos_jugador:
			valor = datos_jugador[columna]
			# Solo agregar si es un número válido y no es texto
			if pd.notna(valor) and valor is not None and isinstance(valor, (int, float)):
				valores.append(float(valor))
				etiquetas.append(etiqueta)
	
	if not valores:
		# Si no hay Z-Scores en Excel, mostrar mensaje
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Z-Scores no disponibles en Excel</b><br>Usar función automática",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=14, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=400
		)
		return fig
	
	# Crear el radar chart
	fig = go.Figure()
	
	fig.add_trace(go.Scatterpolar(
		r=valores,
		theta=etiquetas,
		fill='toself',
		name=jugador_nombre,
		line=dict(color=COLORES['rojo_colon'], width=3),
		fillcolor="rgba(220, 38, 38, 0.25)",
		marker=dict(
			size=8,
			color=COLORES['rojo_colon'],
			line=dict(width=2, color="white")
		),
		hovertemplate='<b>%{theta}</b><br>Z-Score: %{r:.2f}<extra></extra>'
	))
	
	# Agregar leyenda interpretativa integrada
	fig.add_annotation(
		text="<b>Interpretación Z-Score</b><br>" +
			 "<span style='color: #22c55e;'>Z > +1:</span> Superior al promedio<br>" +
			 "<span style='color: #fbbf24;'>Z = 0:</span> Rendimiento promedio<br>" +
			 "<span style='color: #ef4444;'>Z < -1:</span> Inferior al promedio",
		x=0.02,
		y=0.98,
		xref="paper",
		yref="paper",
		xanchor="left",
		yanchor="top",
		showarrow=False,
		font=dict(size=11, color="white", family="Roboto"),
		align="left",
		bgcolor="rgba(31, 41, 55, 0.9)",
		bordercolor="rgba(59, 130, 246, 0.8)",
		borderwidth=2,
		borderpad=10,
		opacity=0.95
	)
	
	fig.update_layout(
		polar=dict(
			radialaxis=dict(
				visible=True,
				range=[-3, 3],
				tickfont=dict(size=10, color="white"),
				gridcolor="rgba(255,255,255,0.3)",
				linecolor="rgba(255,255,255,0.5)"
			),
			angularaxis=dict(
				tickfont=dict(size=11, color="white", family="Roboto"),
				linecolor="rgba(255,255,255,0.5)",
				gridcolor="rgba(255,255,255,0.2)"
			),
			bgcolor=COLORES['fondo_oscuro']
		),
		showlegend=False,
		title=dict(
			text=f"Perfil Z-Score - {jugador_nombre}",
			font=dict(size=16, color="white", family="Roboto", weight="bold"),
			x=0.5,
			xanchor="center"
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Roboto"),
		height=500,
		margin=dict(t=60, b=40, l=40, r=40)
	)
	
	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando radar Z-Score simplificado...")
def crear_radar_zscore_simple(zscores_radar, jugador_nombre):
	"""
	Crea un radar chart simplificado estilo deportivo (máximo 5 métricas)
	Similar al estilo de la imagen de referencia con colores del club
	
	Args:
		zscores_radar: Dict con Z-Scores calculados (máximo 5 métricas)
		jugador_nombre: Nombre del jugador
		
	Returns:
		Figura de Plotly con radar chart simplificado
	"""
	if not zscores_radar or len(zscores_radar) == 0:
		# Crear gráfico vacío si no hay datos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin datos para radar Z-Score</b><br>Verificar métricas del jugador",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Extraer datos para el radar
	valores = []
	etiquetas = []
	valores_originales = []
	medias_poblacion = []
	
	# Orden específico para mejor visualización
	orden_metricas = ['CUAD', 'ISQ Wollin', 'IMTP', 'CMJ Propulsiva', 'CMJ Frenado']
	
	for metrica in orden_metricas:
		if metrica in zscores_radar:
			data = zscores_radar[metrica]
			valores.append(data['zscore'])
			etiquetas.append(metrica)
			valores_originales.append(data['valor_original'])
			medias_poblacion.append(data['media_poblacion'])
	
	if not valores:
		# Sin valores válidos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin Z-Scores válidos</b><br>Verificar datos del jugador",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Crear el radar chart estilo deportivo
	fig = go.Figure()
	
	# Línea de referencia del grupo (media = 0)
	valores_grupo = [0] * len(etiquetas)  # Media del grupo siempre es 0 en Z-Score
	fig.add_trace(go.Scatterpolar(
		r=valores_grupo,
		theta=etiquetas,
		fill='toself',
		name='Media del Grupo',
		line=dict(
			color="rgba(59, 130, 246, 0.6)", 
			width=3,
			dash='dash'
		),
		fillcolor="rgba(59, 130, 246, 0.15)",
		marker=dict(
			size=8,
			color="rgba(59, 130, 246, 0.6)",
			line=dict(width=2, color="white"),
			opacity=0.8,
			symbol="circle"
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  'Media del Grupo (Z=0)<br>' +
					  '<extra></extra>'
	))
	
	# Área rellena principal (jugador)
	fig.add_trace(go.Scatterpolar(
		r=valores,
		theta=etiquetas,
		fill='toself',
		name=jugador_nombre,
		line=dict(
			color="rgba(220, 38, 38, 1)", 
			width=5
		),
		fillcolor="rgba(220, 38, 38, 0.4)",
		marker=dict(
			size=15,
			color="rgba(220, 38, 38, 1)",
			line=dict(width=4, color="white"),
			opacity=1.0,
			symbol="circle"
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  'Z-Score: %{r:.2f}<br>' +
					  'Valor: %{customdata[0]:.1f}<br>' +
					  'Media: %{customdata[1]:.1f}<br>' +
					  '<extra></extra>',
		customdata=list(zip(valores_originales, medias_poblacion))
	))
	
	# Eliminar completamente las líneas de referencia problemáticas
	# Solo usar las grillas nativas del radar de Plotly
	
	# Configuración del layout estilo deportivo mejorado
	fig.update_layout(
		polar=dict(
			radialaxis=dict(
				visible=True,
				range=[-2.5, 2.5],
				tickvals=[-2, -1, 0, 1, 2],
				ticktext=['-2', '-1', '0', '+1', '+2'],
				tickfont=dict(size=14, color="rgba(255,255,255,0.9)", family="Roboto"),
				gridcolor="rgba(255,255,255,0.3)",
				linecolor="rgba(255,255,255,0.5)",
				showticklabels=True,
				tickangle=0
			),
			angularaxis=dict(
				tickfont=dict(size=16, color="white", family="Source Sans Pro", weight=600),
				linecolor="rgba(255,255,255,0.6)",
				gridcolor="rgba(255,255,255,0.3)",
				rotation=90,  # CUAD arriba
				direction="clockwise"
			),
			bgcolor=COLORES['fondo_oscuro']
		),
		showlegend=False,
		title=dict(
			text=f"<b style='color: rgba(220, 38, 38, 1); font-size: 24px;'>{jugador_nombre}</b><br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Perfil Z-Score vs Grupo</span>",
			font=dict(size=20, color="white", family="Source Sans Pro", weight=600),
			x=0.5,
			xanchor="center",
			y=0.95
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Source Sans Pro"),
		height=600,
		margin=dict(t=100, b=80, l=80, r=80)  # Márgenes equilibrados sin leyenda
	)
	
	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico grupal de fuerza...")
def crear_grafico_multifuerza_grupal(estadisticas_grupales, metricas_seleccionadas, categoria):
	"""Crea gráfico de multifuerza GRUPAL con medias del grupo"""
	
	# Separar métricas bilaterales y totales
	metricas_bilaterales = []
	metricas_totales = []
	barras_der, barras_izq, nombres_bilaterales = [], [], []
	valores_totales, nombres_totales = [], []
	lsi_labels = {}

	for metrica in metricas_seleccionadas:
		if metrica in estadisticas_grupales:
			# Métricas totales (no bilaterales)
			if metrica in ["IMTP Total", "CMJ FP Total", "CMJ FF Total"]:
				val_total = estadisticas_grupales[metrica]['media_total']
				valores_totales.append(val_total)
				nombres_totales.append(metrica)
				metricas_totales.append(metrica)
				
			# Métricas bilaterales tradicionales
			else:
				val_der = estadisticas_grupales[metrica]['media_der']
				val_izq = estadisticas_grupales[metrica]['media_izq']
				barras_der.append(val_der)
				barras_izq.append(val_izq)
				nombres_bilaterales.append(metrica)
				metricas_bilaterales.append(metrica)
				
				# Calcular LSI grupal para métricas bilaterales
				if val_der > 0 and val_izq > 0:
					lsi_val = (min(val_der, val_izq) / max(val_der, val_izq)) * 100
					lsi_labels[metrica] = lsi_val

	fig = go.Figure()

	# Agregar trazas para métricas bilaterales (si existen)
	if nombres_bilaterales:
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_der,
			name="🔴 Derecho (Grupo)",
			marker=dict(
				color="rgba(220, 38, 38, 0.9)",  # Rojo igual al individual
				pattern=dict(
					shape="",
					bgcolor="rgba(220, 38, 38, 0.3)",
					fgcolor="rgba(220, 38, 38, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in barras_der],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>🔴 Derecho (Grupo)</b><br>%{x}: %{y:.0f} N<br><i>Media grupal</i><extra></extra>',
			offsetgroup=1,
			hoverlabel=dict(
				bgcolor="rgba(220, 38, 38, 0.9)",
				bordercolor="rgba(220, 38, 38, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_izq,
			name="⚫ Izquierdo (Grupo)",
			marker=dict(
				color="rgba(31, 41, 55, 0.9)",  # Negro igual al individual
				pattern=dict(
					shape="",
					bgcolor="rgba(31, 41, 55, 0.3)",
					fgcolor="rgba(31, 41, 55, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in barras_izq],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>⚫ Izquierdo (Grupo)</b><br>%{x}: %{y:.0f} N<br><i>Media grupal</i><extra></extra>',
			offsetgroup=2,
			hoverlabel=dict(
				bgcolor="rgba(31, 41, 55, 0.9)",
				bordercolor="rgba(31, 41, 55, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# Agregar traza para métricas totales (si existen) - UNA SOLA BARRA CENTRADA
	if nombres_totales:
		fig.add_trace(go.Bar(
			x=nombres_totales,
			y=valores_totales,
			name="🟡 Total (Grupo)",
			marker=dict(
				color="rgba(255, 193, 7, 0.9)",  # Color dorado para totales
				pattern=dict(
					shape="",
					bgcolor="rgba(255, 193, 7, 0.3)",
					fgcolor="rgba(255, 193, 7, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in valores_totales],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>🟡 Total (Grupo)</b><br>%{x}: %{y:.0f} N<br><i>Media grupal bilateral</i><extra></extra>',
			offsetgroup=3,
			hoverlabel=dict(
				bgcolor="rgba(255, 193, 7, 0.9)",
				bordercolor="rgba(255, 193, 7, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# LSI annotations - SOLO PARA MÉTRICAS BILATERALES GRUPALES
	for i, name in enumerate(nombres_bilaterales):
		lsi_val = lsi_labels.get(name)
		
		if lsi_val and lsi_val > 0:
			# Determinar color según rango LSI
			if 90 <= lsi_val <= 110:  # Zona óptima
				lsi_color = COLORES['verde_optimo']
				border_color = "rgba(50, 205, 50, 1)"
			elif 80 <= lsi_val < 90 or 110 < lsi_val <= 120:  # Zona de alerta
				lsi_color = COLORES['naranja_alerta']
				border_color = "rgba(255, 165, 0, 1)"
			else:  # Zona de riesgo
				lsi_color = COLORES['rojo_riesgo']
				border_color = "rgba(255, 69, 0, 1)"
			
			fig.add_annotation(
				text=f"<b>LSI Grupal: {lsi_val:.1f}%</b>",
				x=name,
				y=max(barras_der[i], barras_izq[i]) * 1.55,
				showarrow=False,
				font=dict(size=11, color="white", family="Roboto", weight="bold"),
				xanchor="center",
				align="center",
				bgcolor=lsi_color,
				bordercolor=border_color,
				borderwidth=2,
				borderpad=8,
				opacity=0.95
			)
	
	# Agregar logo del club como marca de agua
	try:
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		fig.add_layout_image(
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

	fig.update_layout(
		barmode="group",
		bargap=0.3,
		bargroupgap=0.1,
		title=dict(
			text=f"Perfil Grupal – {categoria}<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Fuerza – Medias Grupales</span>",
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
			categoryarray=nombres_bilaterales + nombres_totales
		),
		yaxis=dict(
			title=dict(
				text="Fuerza (N)", 
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
		height=650,
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

	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando radar grupal...")
def crear_radar_zscore_grupal(datos_grupo_radar, nombre_grupo):
	"""
	Crea un radar chart para análisis GRUPAL mostrando solo las medias del grupo
	
	Args:
		datos_grupo_radar: Dict con datos grupales (Z-Score siempre 0)
		nombre_grupo: Nombre del grupo
		
	Returns:
		Figura de Plotly con radar chart grupal
	"""
	if not datos_grupo_radar or len(datos_grupo_radar) == 0:
		# Crear gráfico vacío si no hay datos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin datos para radar grupal</b><br>Verificar métricas del grupo",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Extraer datos para el radar grupal
	valores = []
	etiquetas = []
	valores_originales = []
	
	# Orden específico para mejor visualización
	orden_metricas = ['CUAD', 'ISQ Wollin', 'IMTP', 'CMJ Propulsiva', 'CMJ Frenado']
	
	for metrica in orden_metricas:
		if metrica in datos_grupo_radar:
			data = datos_grupo_radar[metrica]
			valores.append(data['zscore'])  # Siempre 0 para grupo
			etiquetas.append(metrica)
			valores_originales.append(data['valor_original'])
	
	if not valores:
		# Sin valores válidos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin datos válidos para radar grupal</b><br>Verificar datos del grupo",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Crear el radar chart estilo grupal
	fig = go.Figure()
	
	# Área rellena principal (grupo - siempre en el centro)
	fig.add_trace(go.Scatterpolar(
		r=valores,  # Todos los valores son 0 (centro)
		theta=etiquetas,
		fill='toself',
		name=nombre_grupo,
		line=dict(
			color="rgba(220, 38, 38, 1)", 
			width=6
		),
		fillcolor="rgba(220, 38, 38, 0.4)",
		marker=dict(
			size=20,
			color="rgba(220, 38, 38, 1)",
			line=dict(width=4, color="white"),
			opacity=1.0,
			symbol="circle"
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  'Media Grupal: %{customdata:.1f}<br>' +
					  '<i>Línea base del grupo</i><br>' +
					  '<extra></extra>',
		customdata=valores_originales
	))
	
	# Configuración del layout estilo grupal
	fig.update_layout(
		polar=dict(
			radialaxis=dict(
				visible=True,
				range=[-2.5, 2.5],
				tickvals=[-2, -1, 0, 1, 2],
				ticktext=['-2', '-1', '0', '+1', '+2'],
				tickfont=dict(size=14, color="rgba(255,255,255,0.9)", family="Roboto"),
				gridcolor="rgba(255,255,255,0.3)",
				linecolor="rgba(255,255,255,0.5)",
				showticklabels=True,
				tickangle=0
			),
			angularaxis=dict(
				tickfont=dict(size=16, color="white", family="Source Sans Pro", weight=600),
				linecolor="rgba(255,255,255,0.6)",
				gridcolor="rgba(255,255,255,0.3)",
				rotation=90,  # CUAD arriba
				direction="clockwise"
			),
			bgcolor=COLORES['fondo_oscuro']
		),
		showlegend=False,
		title=dict(
			text=f"<b style='color: rgba(220, 38, 38, 1); font-size: 24px;'>{nombre_grupo}</b><br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Perfil Grupal - Medias de Referencia</span>",
			font=dict(size=20, color="white", family="Source Sans Pro", weight=600),
			x=0.5,
			xanchor="center",
			y=0.95
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Source Sans Pro"),
		height=600,
		margin=dict(t=100, b=80, l=80, r=80)
	)
	
	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico de distribución grupal...")
def crear_grafico_distribucion_grupal(estadisticas_radar_grupal, categoria_display):
	"""
	Crea un gráfico de barras con rangos para análisis grupal
	Muestra media, mínimo y máximo de cada métrica del grupo
	
	Args:
		estadisticas_radar_grupal: Dict con estadísticas del grupo
		categoria_display: Nombre amigable de la categoría
		
	Returns:
		Figura de Plotly con gráfico de distribución grupal
	"""
	if not estadisticas_radar_grupal or len(estadisticas_radar_grupal) == 0:
		# Crear gráfico vacío si no hay datos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin datos para distribución grupal</b><br>Verificar métricas del grupo",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Extraer datos para el gráfico
	metricas = []
	medias = []
	minimos = []
	maximos = []
	
	# Orden específico para mejor visualización - TODAS las métricas de fuerza
	orden_metricas = ['CUAD', 'ISQ Wollin', 'IMTP Total', 'CMJ FP Total', 'CMJ FF Total', 'TRIPLE SALTO']
	
	for metrica in orden_metricas:
		for metrica_key, stats in estadisticas_radar_grupal.items():
			if stats['label'] == metrica:
				metricas.append(metrica)
				medias.append(stats['media'])
				minimos.append(stats['minimo'])
				maximos.append(stats['maximo'])
				break
	
	if not metricas:
		# Sin métricas válidas
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin métricas válidas</b><br>Verificar datos del grupo",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Crear el gráfico de barras con rangos
	fig = go.Figure()
	
	# Barras principales (medias del grupo)
	fig.add_trace(go.Bar(
		x=metricas,
		y=medias,
		name="Media del Grupo",
		marker=dict(
			color="rgba(220, 38, 38, 0.8)",
			line=dict(color="rgba(220, 38, 38, 1)", width=2)
		),
		text=[f"{v:.0f}" for v in medias],
		textposition="outside",
		textfont=dict(size=14, color="white", family="Roboto", weight="bold"),
		hovertemplate='<b>%{x}</b><br>' +
					  'Media: %{y:.1f}<br>' +
					  '<extra></extra>',
		hoverlabel=dict(
			bgcolor="rgba(220, 38, 38, 0.9)",
			bordercolor="rgba(220, 38, 38, 1)",
			font=dict(color="white", family="Roboto")
		)
	))
	
	# Sin líneas de referencia - cada métrica tiene su propia escala
	
	# Agregar logo del club como marca de agua
	try:
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		fig.add_layout_image(
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
	
	# Configuración del layout
	fig.update_layout(
		title=dict(
			text=f"<b style='color: rgba(220, 38, 38, 1); font-size: 24px;'>{categoria_display}</b><br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Medias del Grupo</span>",
			font=dict(size=20, color="white", family="Source Sans Pro", weight=600),
			x=0.5,
			xanchor="center",
			y=0.95
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
			tickangle=0
		),
		yaxis=dict(
			title=dict(
				text="Valores", 
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
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Roboto"),
		height=600,
		margin=dict(t=100, b=80, l=80, r=80),
		showlegend=False,  # Simplificado - sin leyenda
		hovermode="x unified"
	)
	
	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico comparativo...")
def crear_grafico_multifuerza_comparativo(datos_jugador_hash, estadisticas_grupales, metricas_seleccionadas, metricas_columnas, jugador_nombre):
	"""Crea gráfico de multifuerza COMPARATIVO (Jugador vs Grupo superpuesto)"""
	# Reconstruir datos del jugador desde hash
	datos_jugador = datos_jugador_hash
	
	# Separar métricas bilaterales y totales
	metricas_bilaterales = []
	metricas_totales = []
	
	# Datos del JUGADOR
	barras_der_jugador, barras_izq_jugador, nombres_bilaterales = [], [], []
	valores_totales_jugador, nombres_totales = [], []
	lsi_labels_jugador = {}
	
	# Datos del GRUPO
	barras_der_grupo, barras_izq_grupo = [], []
	valores_totales_grupo = []

	for metrica in metricas_seleccionadas:
		# Métricas totales (no bilaterales)
		if metrica in ["IMTP Total", "CMJ FP Total", "CMJ FF Total"]:
			# JUGADOR
			col_total = metricas_columnas[metrica][0]
			val_total_jugador = datos_jugador.get(col_total, 0)
			valores_totales_jugador.append(val_total_jugador)
			nombres_totales.append(metrica)
			metricas_totales.append(metrica)
			
			# GRUPO
			if col_total in estadisticas_grupales['media']:
				val_total_grupo = estadisticas_grupales['media'][col_total]
				valores_totales_grupo.append(val_total_grupo)
			else:
				valores_totales_grupo.append(0)
			
		# Métricas bilaterales tradicionales
		else:
			col_der, col_izq = metricas_columnas[metrica]
			
			# JUGADOR
			val_der_jugador = datos_jugador.get(col_der, 0)
			val_izq_jugador = datos_jugador.get(col_izq, 0)
			barras_der_jugador.append(val_der_jugador)
			barras_izq_jugador.append(val_izq_jugador)
			nombres_bilaterales.append(metrica)
			metricas_bilaterales.append(metrica)
			
			# LSI del jugador
			if val_der_jugador > 0 and val_izq_jugador > 0:
				lsi_val_jugador = (min(val_der_jugador, val_izq_jugador) / max(val_der_jugador, val_izq_jugador)) * 100
				lsi_labels_jugador[metrica] = lsi_val_jugador
			
			# GRUPO
			if col_der in estadisticas_grupales['media'] and col_izq in estadisticas_grupales['media']:
				val_der_grupo = estadisticas_grupales['media'][col_der]
				val_izq_grupo = estadisticas_grupales['media'][col_izq]
				barras_der_grupo.append(val_der_grupo)
				barras_izq_grupo.append(val_izq_grupo)
			else:
				barras_der_grupo.append(0)
				barras_izq_grupo.append(0)

	fig = go.Figure()

	# === BARRAS DEL GRUPO (FONDO - SEMITRANSPARENTES) ===
	if nombres_bilaterales:
		# Grupo Derecho
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_der_grupo,
			name="🔵 Grupo Derecho",
			marker=dict(
				color="rgba(59, 130, 246, 0.4)",
				line=dict(color="rgba(59, 130, 246, 0.8)", width=1),
				opacity=0.6
			),
			text=[f"{v:.0f}" for v in barras_der_grupo],
			textposition="outside",
			textfont=dict(size=11, color="rgba(59, 130, 246, 0.9)", family="Roboto"),
			hovertemplate='<b>🔵 Grupo Derecho</b><br>%{x}: %{y:.0f} N<br><i>Media grupal</i><extra></extra>',
			offsetgroup=1,
			hoverlabel=dict(
				bgcolor="rgba(59, 130, 246, 0.9)",
				bordercolor="rgba(59, 130, 246, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

		# Grupo Izquierdo
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_izq_grupo,
			name="🔵 Grupo Izquierdo",
			marker=dict(
				color="rgba(59, 130, 246, 0.3)",
				line=dict(color="rgba(59, 130, 246, 0.6)", width=1),
				opacity=0.5
			),
			text=[f"{v:.0f}" for v in barras_izq_grupo],
			textposition="outside",
			textfont=dict(size=11, color="rgba(59, 130, 246, 0.8)", family="Roboto"),
			hovertemplate='<b>🔵 Grupo Izquierdo</b><br>%{x}: %{y:.0f} N<br><i>Media grupal</i><extra></extra>',
			offsetgroup=2,
			hoverlabel=dict(
				bgcolor="rgba(59, 130, 246, 0.9)",
				bordercolor="rgba(59, 130, 246, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# === BARRAS DEL JUGADOR (PRIMER PLANO - COLORES ORIGINALES) ===
	if nombres_bilaterales:
		# Jugador Derecho
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_der_jugador,
			name=f"🔴 {jugador_nombre} Derecho",
			marker=dict(
				color=COLORES['rojo_colon'],
				pattern=dict(
					shape="",
					bgcolor="rgba(220, 38, 38, 0.3)",
					fgcolor="rgba(220, 38, 38, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in barras_der_jugador],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate=f'<b>🔴 {jugador_nombre} Derecho</b><br>%{{x}}: %{{y:.0f}} N<br><i>Jugador individual</i><extra></extra>',
			offsetgroup=3,
			hoverlabel=dict(
				bgcolor="rgba(220, 38, 38, 0.9)",
				bordercolor="rgba(220, 38, 38, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

		# Jugador Izquierdo
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_izq_jugador,
			name=f"⚫ {jugador_nombre} Izquierdo",
			marker=dict(
				color=COLORES['negro_colon'],
				pattern=dict(
					shape="",
					bgcolor="rgba(31, 41, 55, 0.3)",
					fgcolor="rgba(31, 41, 55, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in barras_izq_jugador],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate=f'<b>⚫ {jugador_nombre} Izquierdo</b><br>%{{x}}: %{{y:.0f}} N<br><i>Jugador individual</i><extra></extra>',
			offsetgroup=4,
			hoverlabel=dict(
				bgcolor="rgba(31, 41, 55, 0.9)",
				bordercolor="rgba(31, 41, 55, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# === MÉTRICAS TOTALES ===
	if nombres_totales:
		# Grupo Total
		fig.add_trace(go.Bar(
			x=nombres_totales,
			y=valores_totales_grupo,
			name="🔵 Grupo Total",
			marker=dict(
				color="rgba(59, 130, 246, 0.4)",
				line=dict(color="rgba(59, 130, 246, 0.8)", width=1),
				opacity=0.6
			),
			text=[f"{v:.0f}" for v in valores_totales_grupo],
			textposition="outside",
			textfont=dict(size=11, color="rgba(59, 130, 246, 0.9)", family="Roboto"),
			hovertemplate='<b>🔵 Grupo Total</b><br>%{x}: %{y:.0f} N<br><i>Media grupal bilateral</i><extra></extra>',
			offsetgroup=5,
			hoverlabel=dict(
				bgcolor="rgba(59, 130, 246, 0.9)",
				bordercolor="rgba(59, 130, 246, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

		# Jugador Total
		fig.add_trace(go.Bar(
			x=nombres_totales,
			y=valores_totales_jugador,
			name=f"🟡 {jugador_nombre} Total",
			marker=dict(
				color="rgba(255, 193, 7, 0.9)",
				pattern=dict(
					shape="",
					bgcolor="rgba(255, 193, 7, 0.3)",
					fgcolor="rgba(255, 193, 7, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f} N" for v in valores_totales_jugador],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate=f'<b>🟡 {jugador_nombre} Total</b><br>%{{x}}: %{{y:.0f}} N<br><i>Valor bilateral combinado</i><extra></extra>',
			offsetgroup=6,
			hoverlabel=dict(
				bgcolor="rgba(255, 193, 7, 0.9)",
				bordercolor="rgba(255, 193, 7, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# === LSI ANNOTATIONS - SOLO PARA EL JUGADOR ===
	for i, name in enumerate(nombres_bilaterales):
		lsi_val_jugador = lsi_labels_jugador.get(name)
		
		if lsi_val_jugador and lsi_val_jugador > 0:
			# Determinar color según rango LSI
			if 90 <= lsi_val_jugador <= 110:
				lsi_color = COLORES['verde_optimo']
				border_color = "rgba(50, 205, 50, 1)"
			elif 80 <= lsi_val_jugador < 90 or 110 < lsi_val_jugador <= 120:
				lsi_color = COLORES['naranja_alerta']
				border_color = "rgba(255, 165, 0, 1)"
			else:
				lsi_color = COLORES['rojo_riesgo']
				border_color = "rgba(255, 69, 0, 1)"
			
			# Calcular altura máxima entre jugador y grupo
			max_altura = max(
				barras_der_jugador[i] if i < len(barras_der_jugador) else 0,
				barras_izq_jugador[i] if i < len(barras_izq_jugador) else 0,
				barras_der_grupo[i] if i < len(barras_der_grupo) else 0,
				barras_izq_grupo[i] if i < len(barras_izq_grupo) else 0
			)
			
			fig.add_annotation(
				text=f"<b>LSI: {lsi_val_jugador:.1f}%</b>",
				x=name,
				y=max_altura * 1.65,
				showarrow=False,
				font=dict(size=11, color="white", family="Roboto", weight="bold"),
				xanchor="center",
				align="center",
				bgcolor=lsi_color,
				bordercolor=border_color,
				borderwidth=2,
				borderpad=8,
				opacity=0.95
			)
	
	# Agregar logo del club como marca de agua
	try:
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		fig.add_layout_image(
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

	fig.update_layout(
		barmode="group",
		bargap=0.2,
		bargroupgap=0.05,
		title=dict(
			text=f"Comparación {jugador_nombre} vs Grupo<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Fuerza – Individual vs Media Grupal</span>",
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
			categoryarray=nombres_bilaterales + nombres_totales
		),
		yaxis=dict(
			title=dict(
				text="Fuerza (N)", 
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
			font=dict(size=11, family="Roboto"),
			bgcolor="rgba(220, 38, 38, 0.2)",
			bordercolor="rgba(220, 38, 38, 0.5)",
			borderwidth=2
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Roboto"),
		height=700,
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

	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando radar comparativo...")
def crear_radar_zscore_comparativo(zscores_jugador, datos_grupo_radar, jugador_nombre, categoria_nombre):
	"""
	Crea un radar chart COMPARATIVO (Jugador vs Grupo superpuesto)
	Combina el jugador individual con la línea base del grupo
	
	Args:
		zscores_jugador: Dict con Z-Scores del jugador individual
		datos_grupo_radar: Dict con datos grupales (Z-Score siempre 0)
		jugador_nombre: Nombre del jugador
		categoria_nombre: Nombre de la categoría/grupo
		
	Returns:
		Figura de Plotly con radar chart comparativo
	"""
	if not zscores_jugador or len(zscores_jugador) == 0:
		# Crear gráfico vacío si no hay datos del jugador
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin datos para radar comparativo</b><br>Verificar métricas del jugador",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Extraer datos para el radar comparativo
	valores_jugador = []
	valores_grupo = []
	etiquetas = []
	valores_originales_jugador = []
	medias_poblacion = []
	
	# Orden específico para mejor visualización
	orden_metricas = ['CUAD', 'ISQ Wollin', 'IMTP', 'CMJ Propulsiva', 'CMJ Frenado']
	
	for metrica in orden_metricas:
		if metrica in zscores_jugador:
			# Datos del jugador
			data_jugador = zscores_jugador[metrica]
			valores_jugador.append(data_jugador['zscore'])
			etiquetas.append(metrica)
			valores_originales_jugador.append(data_jugador['valor_original'])
			medias_poblacion.append(data_jugador['media_poblacion'])
			
			# Datos del grupo (siempre 0 en Z-Score)
			valores_grupo.append(0)  # Media del grupo siempre es 0 en Z-Score
	
	if not valores_jugador:
		# Sin valores válidos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin Z-Scores válidos para comparación</b><br>Verificar datos del jugador",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Crear el radar chart comparativo
	fig = go.Figure()
	
	# === LÍNEA BASE DEL GRUPO (FONDO - SEMITRANSPARENTE) ===
	fig.add_trace(go.Scatterpolar(
		r=valores_grupo,  # Todos los valores son 0 (centro)
		theta=etiquetas,
		fill='toself',
		name=f'Media {categoria_nombre}',
		line=dict(
			color="rgba(59, 130, 246, 0.6)", 
			width=4,
			dash='dash'
		),
		fillcolor="rgba(59, 130, 246, 0.15)",
		marker=dict(
			size=12,
			color="rgba(59, 130, 246, 0.6)",
			line=dict(width=3, color="white"),
			opacity=0.8,
			symbol="circle"
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  'Media del Grupo (Z=0)<br>' +
					  'Línea base de referencia<br>' +
					  '<extra></extra>'
	))
	
	# === ÁREA DEL JUGADOR (PRIMER PLANO - COLORES ORIGINALES) ===
	fig.add_trace(go.Scatterpolar(
		r=valores_jugador,
		theta=etiquetas,
		fill='toself',
		name=jugador_nombre,
		line=dict(
			color="rgba(220, 38, 38, 1)",  # Rojo original del club
			width=5
		),
		fillcolor="rgba(220, 38, 38, 0.4)",
		marker=dict(
			size=15,
			color="rgba(220, 38, 38, 1)",
			line=dict(width=4, color="white"),
			opacity=1.0,
			symbol="circle"
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  f'<b>{jugador_nombre}</b><br>' +
					  'Z-Score: %{r:.2f}<br>' +
					  'Valor: %{customdata[0]:.1f}<br>' +
					  'Media Grupo: %{customdata[1]:.1f}<br>' +
					  '<extra></extra>',
		customdata=list(zip(valores_originales_jugador, medias_poblacion))
	))
	
	# Configuración del layout estilo comparativo
	fig.update_layout(
		polar=dict(
			radialaxis=dict(
				visible=True,
				range=[-2.5, 2.5],
				tickvals=[-2, -1, 0, 1, 2],
				ticktext=['-2', '-1', '0', '+1', '+2'],
				tickfont=dict(size=14, color="rgba(255,255,255,0.9)", family="Roboto"),
				gridcolor="rgba(255,255,255,0.3)",
				linecolor="rgba(255,255,255,0.5)",
				showticklabels=True,
				tickangle=0
			),
			angularaxis=dict(
				tickfont=dict(size=16, color="white", family="Source Sans Pro", weight=600),
				linecolor="rgba(255,255,255,0.6)",
				gridcolor="rgba(255,255,255,0.3)",
				rotation=90,  # CUAD arriba
				direction="clockwise"
			),
			bgcolor=COLORES['fondo_oscuro']
		),
		showlegend=False,
		title=dict(
			text=f"<b style='color: rgba(220, 38, 38, 1); font-size: 24px;'>{jugador_nombre} vs Grupo</b><br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Comparación Individual vs Media Grupal</span>",
			font=dict(size=20, color="white", family="Source Sans Pro", weight=600),
			x=0.5,
			xanchor="center",
			y=0.96
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Source Sans Pro"),
		height=650,
		margin=dict(t=110, b=80, l=80, r=80)
	)
	
	return fig

# ========= FUNCIONES DE MOVILIDAD =========

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico de movilidad...")
def crear_grafico_multimovilidad(datos_jugador_hash, metricas_seleccionadas, metricas_columnas):
	"""Crea gráfico de multimovilidad con cache optimizado - EXACTAMENTE IGUAL A FUERZA"""
	# Reconstruir datos del jugador desde hash
	datos_jugador = datos_jugador_hash
	
	# Solo métricas bilaterales en movilidad (no hay totales)
	barras_der, barras_izq, nombres_bilaterales = [], [], []
	lsi_labels = {}

	for metrica in metricas_seleccionadas:
		col_der, col_izq = metricas_columnas[metrica]
		val_der = datos_jugador.get(col_der, 0)
		val_izq = datos_jugador.get(col_izq, 0)
		barras_der.append(val_der)
		barras_izq.append(val_izq)
		nombres_bilaterales.append(metrica)
		
		# Calcular LSI para métricas bilaterales
		if val_der > 0 and val_izq > 0:
			lsi_val = (min(val_der, val_izq) / max(val_der, val_izq)) * 100
			lsi_labels[metrica] = lsi_val

	fig = go.Figure()

	# Agregar trazas para métricas bilaterales - COLORES EXACTAMENTE IGUALES A FUERZA
	fig.add_trace(go.Bar(
		x=nombres_bilaterales,
		y=barras_der,
		name="🔴 Derecho",
		marker=dict(
			color=COLORES['rojo_colon'],
			pattern=dict(
				shape="",
				bgcolor="rgba(220, 38, 38, 0.3)",
				fgcolor="rgba(220, 38, 38, 1)"
			),
			opacity=0.9
		),
		text=[f"{v:.0f}°" for v in barras_der],
		textposition="outside",
		textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
		hovertemplate='<b>🔴 Derecho</b><br>%{x}: %{y:.0f}°<br><i>Lado dominante</i><extra></extra>',
		offsetgroup=1,
		hoverlabel=dict(
			bgcolor="rgba(220, 38, 38, 0.9)",
			bordercolor="rgba(220, 38, 38, 1)",
			font=dict(color="white", family="Roboto")
		)
	))

	fig.add_trace(go.Bar(
		x=nombres_bilaterales,
		y=barras_izq,
		name="⚫ Izquierdo",
		marker=dict(
			color=COLORES['negro_colon'],
			pattern=dict(
				shape="",
				bgcolor="rgba(31, 41, 55, 0.3)",
				fgcolor="rgba(31, 41, 55, 1)"
			),
			opacity=0.9
		),
		text=[f"{v:.0f}°" for v in barras_izq],
		textposition="outside",
		textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
		hovertemplate='<b>⚫ Izquierdo</b><br>%{x}: %{y:.0f}°<br><i>Lado no dominante</i><extra></extra>',
		offsetgroup=2,
		hoverlabel=dict(
			bgcolor="rgba(31, 41, 55, 0.9)",
			bordercolor="rgba(31, 41, 55, 1)",
			font=dict(color="white", family="Roboto")
		)
	))

	# LSI annotations - EXACTAMENTE IGUAL A FUERZA
	for i, name in enumerate(nombres_bilaterales):
		lsi_val = lsi_labels.get(name)
		
		if lsi_val and lsi_val > 0:
			# Determinar color según rango LSI
			if 90 <= lsi_val <= 110:  # Zona óptima
				lsi_color = COLORES['verde_optimo']
				border_color = "rgba(50, 205, 50, 1)"
			elif 80 <= lsi_val < 90 or 110 < lsi_val <= 120:  # Zona de alerta
				lsi_color = COLORES['naranja_alerta']
				border_color = "rgba(255, 165, 0, 1)"
			else:  # Zona de riesgo
				lsi_color = COLORES['rojo_riesgo']
				border_color = "rgba(255, 69, 0, 1)"
			
			fig.add_annotation(
				text=f"<b>LSI: {lsi_val:.1f}%</b>",
				x=name,
				y=max(barras_der[i], barras_izq[i]) * 1.55,
				showarrow=False,
				font=dict(size=11, color="white", family="Roboto", weight="bold"),
				xanchor="center",
				align="center",
				bgcolor=lsi_color,
				bordercolor=border_color,
				borderwidth=2,
				borderpad=8,
				opacity=0.95
			)
	
	# Agregar logo del club como marca de agua - EXACTAMENTE IGUAL A FUERZA
	try:
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		fig.add_layout_image(
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

	fig.update_layout(
		barmode="group",
		bargap=0.3,
		bargroupgap=0.1,
		title=dict(
			text="Evaluación Física Integral – Atlético Colón<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Movilidad – Bilaterales</span>",
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
			categoryarray=nombres_bilaterales
		),
		yaxis=dict(
			title=dict(
				text="Ángulo (°)", 
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
		height=650,
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

	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando radar Z-Score de movilidad...")
def crear_radar_zscore_simple_movilidad(zscores_radar, jugador_nombre):
	"""
	Crea un radar chart simplificado para movilidad - EXACTAMENTE IGUAL A FUERZA
	
	Args:
		zscores_radar: Dict con Z-Scores calculados (máximo 3 métricas de movilidad)
		jugador_nombre: Nombre del jugador
		
	Returns:
		Figura de Plotly con radar chart simplificado
	"""
	if not zscores_radar or len(zscores_radar) == 0:
		# Crear gráfico vacío si no hay datos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin datos para radar Z-Score</b><br>Verificar métricas del jugador",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Extraer datos para el radar
	valores = []
	etiquetas = []
	valores_originales = []
	medias_poblacion = []
	
	# Orden específico para mejor visualización de movilidad
	orden_metricas = ['AKE', 'THOMAS', 'LUNGE']
	
	for metrica in orden_metricas:
		if metrica in zscores_radar:
			data = zscores_radar[metrica]
			valores.append(data['zscore'])
			etiquetas.append(metrica)
			valores_originales.append(data['valor_original'])
			medias_poblacion.append(data['media_poblacion'])
	
	if not valores:
		# Sin valores válidos
		fig = go.Figure()
		fig.add_annotation(
			text="<b>Sin Z-Scores válidos</b><br>Verificar datos del jugador",
			x=0.5, y=0.5,
			xref="paper", yref="paper",
			showarrow=False,
			font=dict(size=16, color="white", family="Roboto"),
			align="center"
		)
		fig.update_layout(
			plot_bgcolor=COLORES['fondo_oscuro'],
			paper_bgcolor=COLORES['fondo_oscuro'],
			height=500
		)
		return fig
	
	# Crear el radar chart estilo deportivo - EXACTAMENTE IGUAL A FUERZA
	fig = go.Figure()
	
	# Línea de referencia del grupo (media = 0)
	valores_grupo = [0] * len(etiquetas)  # Media del grupo siempre es 0 en Z-Score
	fig.add_trace(go.Scatterpolar(
		r=valores_grupo,
		theta=etiquetas,
		fill='toself',
		name='Media del Grupo',
		line=dict(
			color="rgba(59, 130, 246, 0.6)", 
			width=3,
			dash='dash'
		),
		fillcolor="rgba(59, 130, 246, 0.15)",
		marker=dict(
			size=8,
			color="rgba(59, 130, 246, 0.6)",
			line=dict(width=2, color="white"),
			opacity=0.8,
			symbol="circle"
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  'Media del Grupo (Z=0)<br>' +
					  '<extra></extra>'
	))
	
	# Área rellena principal (jugador) - COLORES EXACTAMENTE IGUALES A FUERZA
	fig.add_trace(go.Scatterpolar(
		r=valores,
		theta=etiquetas,
		fill='toself',
		name=jugador_nombre,
		line=dict(
			color="rgba(220, 38, 38, 1)", 
			width=5
		),
		fillcolor="rgba(220, 38, 38, 0.4)",
		marker=dict(
			size=15,
			color="rgba(220, 38, 38, 1)",
			line=dict(width=4, color="white"),
			opacity=1.0,
			symbol="circle"
		),
		hovertemplate='<b>%{theta}</b><br>' +
					  'Z-Score: %{r:.2f}<br>' +
					  'Valor: %{customdata[0]:.1f}°<br>' +
					  'Media: %{customdata[1]:.1f}°<br>' +
					  '<extra></extra>',
		customdata=list(zip(valores_originales, medias_poblacion))
	))
	
	# Configuración del layout estilo deportivo mejorado - EXACTAMENTE IGUAL A FUERZA
	fig.update_layout(
		polar=dict(
			radialaxis=dict(
				visible=True,
				range=[-2.5, 2.5],
				tickvals=[-2, -1, 0, 1, 2],
				ticktext=['-2', '-1', '0', '+1', '+2'],
				tickfont=dict(size=14, color="rgba(255,255,255,0.9)", family="Roboto"),
				gridcolor="rgba(255,255,255,0.3)",
				linecolor="rgba(255,255,255,0.5)",
				showticklabels=True,
				tickangle=0
			),
			angularaxis=dict(
				tickfont=dict(size=16, color="white", family="Source Sans Pro", weight=600),
				linecolor="rgba(255,255,255,0.6)",
				gridcolor="rgba(255,255,255,0.3)",
				rotation=90,  # AKE arriba
				direction="clockwise"
			),
			bgcolor=COLORES['fondo_oscuro']
		),
		showlegend=False,
		title=dict(
			text=f"<b style='color: rgba(220, 38, 38, 1); font-size: 24px;'>{jugador_nombre}</b><br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Perfil Z-Score Movilidad vs Grupo</span>",
			font=dict(size=20, color="white", family="Source Sans Pro", weight=600),
			x=0.5,
			xanchor="center",
			y=0.95
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Source Sans Pro"),
		height=600,
		margin=dict(t=100, b=80, l=80, r=80)  # Márgenes equilibrados sin leyenda
	)
	
	return fig

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico grupal de movilidad...")
def crear_grafico_multimovilidad_grupal(estadisticas_grupales, metricas_seleccionadas, categoria):
	"""Crea gráfico de multimovilidad GRUPAL con medias del grupo"""
	
	# Separar métricas bilaterales (no hay totales en movilidad)
	metricas_bilaterales = []
	barras_der, barras_izq, nombres_bilaterales = [], [], []
	lsi_labels = {}

	for metrica in metricas_seleccionadas:
		if metrica in estadisticas_grupales:
			# Todas las métricas de movilidad son bilaterales
			val_der = estadisticas_grupales[metrica]['media_der']
			val_izq = estadisticas_grupales[metrica]['media_izq']
			barras_der.append(val_der)
			barras_izq.append(val_izq)
			nombres_bilaterales.append(metrica)
			metricas_bilaterales.append(metrica)
			
			# Calcular LSI grupal para métricas bilaterales
			if val_der > 0 and val_izq > 0:
				lsi_val = (min(val_der, val_izq) / max(val_der, val_izq)) * 100
				lsi_labels[metrica] = lsi_val

	fig = go.Figure()

	# Agregar trazas para métricas bilaterales
	if nombres_bilaterales:
		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_der,
			name="🔴 Derecho (Grupo)",
			marker=dict(
				color="rgba(220, 38, 38, 0.9)",  # Rojo igual al individual
				pattern=dict(
					shape="",
					bgcolor="rgba(220, 38, 38, 0.3)",
					fgcolor="rgba(220, 38, 38, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f}°" for v in barras_der],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>🔴 Derecho (Grupo)</b><br>%{x}: %{y:.0f}°<br><i>Media grupal</i><extra></extra>',
			offsetgroup=1,
			hoverlabel=dict(
				bgcolor="rgba(220, 38, 38, 0.9)",
				bordercolor="rgba(220, 38, 38, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

		fig.add_trace(go.Bar(
			x=nombres_bilaterales,
			y=barras_izq,
			name="⚫ Izquierdo (Grupo)",
			marker=dict(
				color="rgba(31, 41, 55, 0.9)",  # Negro igual al individual
				pattern=dict(
					shape="",
					bgcolor="rgba(31, 41, 55, 0.3)",
					fgcolor="rgba(31, 41, 55, 1)"
				),
				opacity=0.9
			),
			text=[f"{v:.0f}°" for v in barras_izq],
			textposition="outside",
			textfont=dict(size=13, color="white", family="Roboto", weight="bold"),
			hovertemplate='<b>⚫ Izquierdo (Grupo)</b><br>%{x}: %{y:.0f}°<br><i>Media grupal</i><extra></extra>',
			offsetgroup=2,
			hoverlabel=dict(
				bgcolor="rgba(31, 41, 55, 0.9)",
				bordercolor="rgba(31, 41, 55, 1)",
				font=dict(color="white", family="Roboto")
			)
		))

	# LSI annotations - SOLO PARA MÉTRICAS BILATERALES GRUPALES
	for i, name in enumerate(nombres_bilaterales):
		lsi_val = lsi_labels.get(name)
		
		if lsi_val and lsi_val > 0:
			# Determinar color según rango LSI
			if 90 <= lsi_val <= 110:  # Zona óptima
				lsi_color = COLORES['verde_optimo']
				border_color = "rgba(50, 205, 50, 1)"
			elif 80 <= lsi_val < 90 or 110 < lsi_val <= 120:  # Zona de alerta
				lsi_color = COLORES['naranja_alerta']
				border_color = "rgba(255, 165, 0, 1)"
			else:  # Zona de riesgo
				lsi_color = COLORES['rojo_riesgo']
				border_color = "rgba(255, 69, 0, 1)"
			
			fig.add_annotation(
				text=f"<b>LSI Grupal: {lsi_val:.1f}%</b>",
				x=name,
				y=max(barras_der[i], barras_izq[i]) * 1.55,
				showarrow=False,
				font=dict(size=11, color="white", family="Roboto", weight="bold"),
				xanchor="center",
				align="center",
				bgcolor=lsi_color,
				bordercolor=border_color,
				borderwidth=2,
				borderpad=8,
				opacity=0.95
			)
	
	# Agregar logo del club como marca de agua
	try:
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		fig.add_layout_image(
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

	fig.update_layout(
		barmode="group",
		bargap=0.3,
		bargroupgap=0.1,
		title=dict(
			text=f"Perfil Grupal – {categoria}<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Métricas de Movilidad – Medias Grupales</span>",
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
			categoryarray=nombres_bilaterales
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
		height=650,
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

	return fig
