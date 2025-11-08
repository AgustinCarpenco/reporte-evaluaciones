"""
Módulo de visualizaciones - Gráficos y charts
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config.settings import CACHE_TTL, COLORES, Z_SCORE_METRICAS, PLOTLY_CONFIG
from utils.ui_utils import get_base64_image

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando gráfico de fuerza...")
def crear_grafico_multifuerza(datos_jugador_hash, metricas_seleccionadas, metricas_columnas):
	"""Crea gráfico de multifuerza con cache optimizado"""
	# Reconstruir datos del jugador desde hash
	datos_jugador = datos_jugador_hash
	barras_der, barras_izq, nombres = [], [], []
	lsi_labels = {}

	for metrica in metricas_seleccionadas:
		# Métricas totales (no bilaterales)
		if metrica in ["IMTP Total", "CMJ FP Total", "CMJ FF Total"]:
			col_total = metricas_columnas[metrica][0]  # Usar la primera columna (son iguales)
			val_total = datos_jugador.get(col_total, 0)
			
			# Para métricas totales, mostrar como una sola barra centrada
			barras_der.append(val_total)
			barras_izq.append(0)  # No hay lado izquierdo para totales
			nombres.append(metrica)
			
		# Métricas bilaterales tradicionales
		else:
			col_der, col_izq = metricas_columnas[metrica]
			val_der = datos_jugador.get(col_der, 0)
			val_izq = datos_jugador.get(col_izq, 0)
			barras_der.append(val_der)
			barras_izq.append(val_izq)
			nombres.append(metrica)
			
			# Calcular LSI para métricas bilaterales
			if val_der > 0 and val_izq > 0:
				lsi_val = (min(val_der, val_izq) / max(val_der, val_izq)) * 100
				lsi_labels[metrica] = lsi_val

	fig = go.Figure()

	fig.add_trace(go.Bar(
		x=nombres,
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
		x=nombres,
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

	# LSI annotations - USANDO CÁLCULOS AUTOMÁTICOS
	for name in nombres:
		lsi_val = lsi_labels.get(name)
		
		# Solo mostrar LSI para métricas bilaterales (no para totales)
		if lsi_val and lsi_val > 0 and name not in ["IMTP Total", "CMJ FP Total", "CMJ FF Total"]:
			idx = nombres.index(name)
			
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
				y=max(barras_der[idx], barras_izq[idx]) * 1.55,
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
			text="⚽ Evaluación Física Integral – Atlético Colón ⚽<br><span style='font-size:16px; color:rgba(255,255,255,0.8);'>Comparación Derecha/Izquierda – Métricas de Fuerza</span>",
			font=dict(size=18, family="Roboto", weight="bold", color="rgba(220, 38, 38, 1)"),
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
			categoryarray=nombres
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

@st.cache_data(ttl=CACHE_TTL['graficos'], show_spinner="Generando radar Z-Score...")
def crear_radar_zscore(datos_jugador_hash, jugador_nombre):
	"""Crea un radar chart con los Z-Scores del jugador seleccionado - Optimizado con cache"""
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
