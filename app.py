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
from modules.fuerza_analysis import analizar_fuerza

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
		<h2 style='margin: 0; color: white; font-weight: bold;'>
			Perfil Individual - {jugador}
		</h2>
		<p style='margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 16px;'>
			Análisis de {seccion} - Categoría: {categoria}
		</p>
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
			st.markdown("### 🔧 Módulo en Desarrollo")
			st.info("El análisis de movilidad estará disponible próximamente.")
			
		elif seccion == "Funcionalidad":
			st.markdown("### 🔧 Módulo en Desarrollo") 
			st.info("El análisis de funcionalidad estará disponible próximamente.")
	
	elif vista == "Perfil del Grupo":
		# Header de sección grupal
		st.markdown(f"""
		<div style='background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(16, 185, 129, 0.2)); 
					padding: 20px; border-radius: 15px; margin-bottom: 25px; 
					border-left: 5px solid rgba(59, 130, 246, 1);'>
			<h2 style='margin: 0; color: white; font-weight: bold;'>
				👥 Perfil del Grupo - {categoria}
			</h2>
			<p style='margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 16px;'>
				Análisis agregado de {seccion} - Valores promedio y estadísticas grupales
			</p>
		</div>
		""", unsafe_allow_html=True)
		
		# Análisis por sección
		if seccion == "Fuerza":
			st.markdown("### 🔧 Módulo en Desarrollo")
			st.info("El análisis grupal de fuerza estará disponible próximamente.")
			
		elif seccion == "Movilidad":
			st.markdown("### 🔧 Módulo en Desarrollo")
			st.info("El análisis grupal de movilidad estará disponible próximamente.")
			
		elif seccion == "Funcionalidad":
			st.markdown("### 🔧 Módulo en Desarrollo") 
			st.info("El análisis grupal de funcionalidad estará disponible próximamente.")
		
	elif vista == "Comparación Jugador vs Grupo":
		# Header de sección comparativa
		crear_header_seccion(seccion, jugador, categoria)
		
		# Obtener datos del jugador seleccionado
		datos_jugador = df[(df["categoria"] == categoria) & (df["Deportista"] == jugador)].iloc[0]
		
		# Análisis por sección
		if seccion == "Fuerza":
			st.markdown("### 🔧 Módulo en Desarrollo")
			st.info("La comparación de fuerza estará disponible próximamente.")
			
		elif seccion == "Movilidad":
			st.markdown("### 🔧 Módulo en Desarrollo")
			st.info("La comparación de movilidad estará disponible próximamente.")
			
		elif seccion == "Funcionalidad":
			st.markdown("### 🔧 Módulo en Desarrollo") 
			st.info("La comparación de funcionalidad estará disponible próximamente.")
	
	else:
		st.warning("Esta visualización detallada está disponible solo en el modo 'Perfil del Jugador'.")
	
	# Footer
	crear_footer()
	
	# Manejo del botón exportar
	if exportar:
		st.success("🔧 Funcionalidad de exportación en desarrollo")

if __name__ == "__main__":
	main()
