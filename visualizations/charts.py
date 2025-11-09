"""
Módulo de visualizaciones - Gráficos y charts
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from config.settings import CACHE_TTL, COLORES, Z_SCORE_METRICAS, METRICAS_ZSCORE_FUERZA, METRICAS_ZSCORE_RADAR_SIMPLE, ESCUDO_PATH
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
				tickfont=dict(size=16, color="white", family="Roboto", weight="bold"),
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
			font=dict(size=20, color="white", family="Roboto", weight="bold"),
			x=0.5,
			xanchor="center",
			y=0.95
		),
		plot_bgcolor=COLORES['fondo_oscuro'],
		paper_bgcolor=COLORES['fondo_oscuro'],
		font=dict(color="white", family="Roboto"),
		height=600,
		margin=dict(t=100, b=80, l=80, r=80)  # Márgenes equilibrados sin leyenda
	)
	
	return fig
