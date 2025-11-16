"""
Aplicación principal refactorizada - Evaluación Física Integral
Club Atlético Colón
"""

import streamlit as st

# Importar módulos refactorizados
from config.settings import DATA_PATH
from utils.ui_utils import inicializar_session_state, aplicar_estilos_css, crear_header_principal, crear_footer, configurar_tema_oscuro
from utils.data_utils import cargar_datos_optimizado
from components.sidebar import crear_sidebar
from modules.fuerza_analysis import analizar_fuerza, analizar_fuerza_grupal, analizar_fuerza_comparativo
from modules.movilidad_analysis import (
	analizar_movilidad,
	analizar_movilidad_grupal,
	analizar_movilidad_comparativo,
)
from utils.pdf_report import construir_contexto_reporte_perfil, generar_pdf_reporte

# ========= CONFIGURACIÓN DE PÁGINA ==========
st.set_page_config(
	page_title="Evaluación Física Integral - Atlético Colón",
	page_icon="⚽",
	layout="wide",
	initial_sidebar_state="expanded"
)

def crear_header_seccion(seccion, jugador, categoria):
	"""Crea header de sección para análisis individual"""
	st.markdown(f"""
	<div style='background: linear-gradient(135deg, rgba(220, 38, 38, 0.2), rgba(31, 41, 55, 0.2)); 
				padding: 20px; border-radius: 15px; margin-bottom: 40px; margin-top: 30px;
				border-left: 5px solid rgba(220, 38, 38, 1);'>
		<h2 style='margin: 0; color: white; font-family: "Source Sans Pro", sans-serif; font-weight: 600; font-size: 1.5rem; line-height: 1.2; padding: 0.75rem 0 1rem;'>
			Perfil Individual<br><br>{jugador}
		</h2>
	</div>
	""", unsafe_allow_html=True)

def main():
	"""Función principal de la aplicación"""
	
	# Configurar tema oscuro ANTES que todo
	configurar_tema_oscuro()
	
	# Inicializar configuración
	inicializar_session_state()
	aplicar_estilos_css()
	
	# Cargar datos
	df = cargar_datos_optimizado(DATA_PATH)
	
	# Crear sidebar y obtener selecciones
	categoria, jugador, vista, seccion, exportar = crear_sidebar(df)
	
	# Crear header principal
	crear_header_principal()
	
	# ========= CONTENIDO PRINCIPAL ==========
	if vista == "Perfil del Jugador":
		# Header de sección
		crear_header_seccion(seccion, jugador, categoria)
		
		# Obtener datos del jugador seleccionado
		datos_jugador = df[(df["categoria"] == categoria) & (df["Deportista"] == jugador)].iloc[0]
		
		# Análisis por sección
		if seccion == "Fuerza":
			analizar_fuerza(df, datos_jugador, jugador, categoria)
			
		elif seccion == "Movilidad":
			analizar_movilidad(df, datos_jugador, jugador, categoria)
	
	elif vista == "Perfil del Grupo":
		# Header de sección grupal - EXACTAMENTE IGUAL AL INDIVIDUAL
		st.markdown(f"""
		<div style='background: linear-gradient(135deg, rgba(220, 38, 38, 0.2), rgba(31, 41, 55, 0.2)); 
					padding: 20px; border-radius: 15px; margin-bottom: 40px; margin-top: 30px;
					border-left: 5px solid rgba(220, 38, 38, 1);'>
			<h2 style='margin: 0; color: white; font-family: "Source Sans Pro", sans-serif; font-weight: 600; font-size: 1.5rem; line-height: 1.2; padding: 0.75rem 0 1rem;'>
				Perfil del Grupo
			</h2>
		</div>
		""", unsafe_allow_html=True)
		
		# Análisis por sección
		if seccion == "Fuerza":
			analizar_fuerza_grupal(df, categoria)
			
		elif seccion == "Movilidad":
			analizar_movilidad_grupal(df, categoria)
		
	elif vista == "Comparación Jugador vs Grupo":
		# Header de sección comparativa
		crear_header_seccion(seccion, jugador, categoria)
		
		# Obtener datos del jugador seleccionado
		datos_jugador = df[(df["categoria"] == categoria) & (df["Deportista"] == jugador)].iloc[0]
		
		# Análisis por sección
		if seccion == "Fuerza":
			analizar_fuerza_comparativo(df, datos_jugador, jugador, categoria)
		
		elif seccion == "Movilidad":
			analizar_movilidad_comparativo(df, datos_jugador, jugador, categoria)
	
	else:
		st.warning("Esta visualización detallada está disponible solo en el modo 'Perfil del Jugador'.")
	
	# Footer
	crear_footer()
	
	# Manejo del botón exportar (solo Perfil del Jugador)
	if exportar and vista == "Perfil del Jugador":
		try:
			# Obtener datos actualizados del jugador
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
				fecha=fecha_str,
			)
			pdf_bytes = generar_pdf_reporte(contexto)

			st.download_button(
				label="📄 Descargar informe en PDF",
				data=pdf_bytes,
				file_name=f"{jugador}_{seccion}_perfil.pdf",
				mime="application/pdf",
			)
		except Exception as e:
			st.error(f"No se pudo generar el PDF del reporte: {e}")

if __name__ == "__main__":
	main()
