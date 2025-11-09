"""
Utilidades para interfaz de usuario
"""

import base64
import streamlit as st
from functools import lru_cache
from config.settings import ESCUDO_PATH

@lru_cache(maxsize=32)
def get_base64_image(image_path):
	"""Convierte imagen a base64 con cache LRU"""
	with open(image_path, "rb") as img_file:
		encoded = base64.b64encode(img_file.read()).decode()
	return encoded

def inicializar_session_state():
	"""Inicializa variables del session state"""
	if 'df_cache' not in st.session_state:
		st.session_state.df_cache = None
	if 'ultimo_jugador' not in st.session_state:
		st.session_state.ultimo_jugador = None
	if 'ultima_categoria' not in st.session_state:
		st.session_state.ultima_categoria = None
	if 'metricas_cache' not in st.session_state:
		st.session_state.metricas_cache = {}

def configurar_tema_oscuro():
	"""Configura el tema oscuro programáticamente"""
	# Configuración del tema mediante st.config
	try:
		import streamlit.config as config
		config.set_option('theme.base', 'dark')
		config.set_option('theme.primaryColor', '#dc2626')
		config.set_option('theme.backgroundColor', '#0e1117')
		config.set_option('theme.secondaryBackgroundColor', '#262730')
		config.set_option('theme.textColor', '#fafafa')
	except:
		pass  # Si no se puede configurar, los CSS harán el trabajo

def aplicar_estilos_css():
	"""
	Aplica estilos mínimos y coherentes con el tema oscuro general del dashboard.
	No modifica los componentes de Streamlit directamente.
	"""
	st.markdown(
		"""
		<style>
		/* Alineación general y tipografía */
		body {
			font-family: 'Inter', sans-serif !important;
		}

		/* Header y footer coherentes con el tema */
		header, footer {
			background-color: transparent !important;
		}
		</style>
		""",
		unsafe_allow_html=True
	)

def crear_header_principal():
	"""Crea el header principal de la aplicación pegado arriba con títulos destacados"""
	escudo_base64 = get_base64_image(ESCUDO_PATH)
	
	# CSS para eliminar padding superior global
	st.markdown('<style>div.block-container{padding-top: 0rem;}</style>', unsafe_allow_html=True)
	
	st.markdown(
		f"""
		<style>
		.header-container {{
			display: flex;
			align-items: center;
			justify-content: center;
			background: linear-gradient(90deg, #7f1d1d, #111827);
			border-radius: 8px;
			padding: 5px 0px;
			margin-top: -25px;
			box-shadow: 0 2px 6px rgba(0,0,0,0.3);
			border: 1px solid rgba(220, 38, 38, 0.3);
			gap: 15px;
		}}
		
		.header-logo {{
			width: 70px;
			filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
		}}
		
		.header-container h1 {{
			color: white;
			font-size: 38px;
			font-weight: 800;
			margin: 2px 0px;
			text-transform: uppercase;
			text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
			line-height: 1;
		}}
		
		.header-container h3 {{
			color: #d1d5db;
			font-size: 20px;
			font-weight: 400;
			margin: 0px;
			line-height: 1;
		}}
		</style>
		
		<div class='header-container'>
			<img src='data:image/png;base64,{escudo_base64}' class='header-logo'/>
			<div>
				<h1>EVALUACIÓN FÍSICA INTEGRAL</h1>
				<h3>Club Atlético Colón</h3>
			</div>
		</div>
		""",
		unsafe_allow_html=True
	)


def crear_footer():
	"""Crea el footer de la aplicación"""
	st.markdown("<br><br>", unsafe_allow_html=True)
	st.markdown("""
	<div style='background: linear-gradient(135deg, rgba(220, 38, 38, 0.9), rgba(17, 24, 39, 0.9)); 
				padding: 15px; border-radius: 10px; text-align: center; margin-top: 40px;
				box-shadow: 0 4px 16px rgba(0,0,0,0.2);'>
		<p style='margin: 0; color: rgba(255,255,255,0.8); font-size: 12px;'>
			© 2025 Club Atlético Colón - Evaluación Física Integral | Desarrollado por Agustin Carpenco v1.0
		</p>
	</div>
	""", unsafe_allow_html=True)


