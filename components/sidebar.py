"""
Componentes de la sidebar
"""

import streamlit as st
from utils.ui_utils import get_base64_image
from utils.data_utils import obtener_jugadores_categoria, limpiar_cache_si_cambio
from config.settings import ESCUDO_PATH
from utils.pdf_report import construir_contexto_reporte_perfil, generar_pdf_reporte

def crear_sidebar(df):
	"""Crea la sidebar completa con todos sus componentes"""
	with st.sidebar:
		# Escudo centrado
		escudo_base64 = get_base64_image(ESCUDO_PATH)
		st.markdown(f"""
		<div style='text-align: center; padding: 20px; margin-bottom: 30px;'>
			<img src='data:image/png;base64,{escudo_base64}' width='80' 
				 style='filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));'/>
		</div>
		""", unsafe_allow_html=True)

		# Selector de categoría con mapeo para nombres amigables
		categorias_originales = df["categoria"].dropna().unique()
		
		# Mapeo simple: nombre_hoja → nombre_mostrar
		mapeo_nombres = {}
		categorias_display = []
		
		for cat_original in categorias_originales:
			# Mapeo específico para la hoja actual y futuras categorías
			if cat_original == "Evaluacion_2910":
				cat_display = "Primer Equipo"
			elif cat_original.lower() in ['reserva', 'reserve']:
				cat_display = "Reserva"
			elif cat_original.lower() in ['4ta', 'cuarta']:
				cat_display = "4ta División"
			else:
				cat_display = cat_original  # Mantener nombre original para otros casos
			
			categorias_display.append(cat_display)
			mapeo_nombres[cat_display] = cat_original
		
		categoria_seleccionada = st.selectbox(
			"Categoría", 
			categorias_display,
			key="categoria_selector",
			help="Selecciona la categoría para filtrar jugadores"
		)
		
		# Obtener el nombre original para filtrar los datos
		categoria = mapeo_nombres[categoria_seleccionada]
		
		# Opciones de análisis (mover antes del selector de deportista)
		vista = st.radio(
			"Tipo de Análisis", 
			["Perfil del Jugador", "Perfil del Grupo", "Comparación Jugador vs Grupo"]
		)
		
		jugadores_filtrados = obtener_jugadores_categoria(df, categoria)
		
		# Selector de deportista - BLOQUEADO para análisis grupal
		if vista == "Perfil del Grupo":
			st.selectbox(
				"Deportista", 
				["--- Análisis Grupal ---"],
				key="jugador_selector_bloqueado",
				disabled=True,
				help="El selector está bloqueado para análisis grupal"
			)
			# Para análisis grupal, usar el primer jugador como placeholder (no se usa)
			jugador = jugadores_filtrados[0] if len(jugadores_filtrados) > 0 else "Sin jugadores"
		else:
			jugador = st.selectbox(
				"Deportista", 
				jugadores_filtrados,
				key="jugador_selector",
				help="Selecciona el deportista para análisis individual"
			)
		
		# Limpiar cache si hay cambio en la selección
		limpiar_cache_si_cambio(jugador, categoria)
		
		# Actualizar session state
		st.session_state.ultimo_jugador = jugador
		st.session_state.ultima_categoria = categoria
		
		seccion = st.radio(
			"Evaluación", 
			["Fuerza", "Movilidad"]
		)

		st.markdown("---")

		# Botón de exportación DIRECTO en la sidebar (mismo PDF para todos los tipos de análisis)
		exportar = False
		if jugador and jugador != "Sin jugadores":
			try:
				# Obtener datos actualizados del jugador seleccionado
				datos_jugador_export = df[(df["categoria"] == categoria) & (df["Deportista"] == jugador)].iloc[0]
				# Extraer fecha desde la columna 'Fecha'
				fecha_valor = datos_jugador_export.get("Fecha", "")
				if hasattr(fecha_valor, "strftime"):
					fecha_str = fecha_valor.strftime("%d/%m/%Y")
				else:
					fecha_str = str(fecha_valor)

				contexto = construir_contexto_reporte_perfil(
					df=df,
					datos_jugador=datos_jugador_export,
					jugador=jugador,
					categoria=categoria,
					seccion=seccion,
					vista=vista,
					fecha=fecha_str,
				)
				pdf_bytes = generar_pdf_reporte(contexto)

				# Nombre de archivo según tipo de análisis
				if vista == "Perfil del Jugador":
					sufijo_vista = "perfil"
				elif vista == "Perfil del Grupo":
					sufijo_vista = "grupo"
				elif vista == "Comparación Jugador vs Grupo":
					sufijo_vista = "comparacion"
				else:
					sufijo_vista = "reporte"

				st.download_button(
					label="📄 Exportar reporte en PDF",
					data=pdf_bytes,
					file_name=f"{jugador}_{seccion}_{sufijo_vista}.pdf",
					mime="application/pdf",
				)
				exportar = True
			except Exception as e:
				# Mostrar mensaje claro si no se puede generar el PDF (por ejemplo, sin datos de fuerza)
				st.warning(str(e))

	return categoria, jugador, vista, seccion, exportar
