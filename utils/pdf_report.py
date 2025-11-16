"""Utilidades para generar reportes PDF del jugador.

Este módulo define la función principal `generar_pdf_reporte` que recibe
los datos ya procesados (jugador, sección, gráficos y tabla) y devuelve
los bytes de un PDF listo para descargar.

Requiere:
- weasyprint
- kaleido (para exportar gráficos de Plotly a imagen, si se usan figuras directamente)

La integración con Streamlit se hará desde app.py usando st.download_button.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import base64
import io
import pandas as pd

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
	from weasyprint import HTML
except ModuleNotFoundError:
	HTML = None  # Se validará en tiempo de ejecución

from modules.fuerza_analysis import obtener_componentes_perfil_fuerza, obtener_componentes_perfil_fuerza_grupal
from modules.movilidad_analysis import obtener_componentes_perfil_movilidad, obtener_componentes_perfil_movilidad_grupal


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"


@dataclass
class ReporteJugadorContexto:
    nombre_jugador: str
    categoria: str
    fecha: str
    seccion: str  # "Fuerza" o "Movilidad"
    vista: str    # "Perfil del Jugador", "Perfil del Grupo", etc.
    graficos_paths: List[str]
    tablas_html: List[str]


def _get_jinja_env() -> Environment:
    """Devuelve un entorno Jinja2 configurado para las plantillas del proyecto."""

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env


def renderizar_html_reporte(contexto: ReporteJugadorContexto, plantilla: str = "reporte_jugador.html") -> str:
    """Renderiza el HTML del reporte del jugador usando Jinja2.

    Parameters
    ----------
    contexto : ReporteJugadorContexto
        Datos ya preparados para el reporte (texto, paths de imágenes, tabla HTML).
    plantilla : str
        Nombre del archivo de plantilla HTML dentro de la carpeta `templates`.

    Returns
    -------
    str
        HTML completo del reporte.
    """

    env = _get_jinja_env()
    template = env.get_template(plantilla)
    html = template.render(
        nombre_jugador=contexto.nombre_jugador,
        categoria=contexto.categoria,
        fecha=contexto.fecha,
        seccion=contexto.seccion,
        vista=contexto.vista,
        graficos_paths=contexto.graficos_paths,
        tablas_html=contexto.tablas_html,
    )
    return html


def generar_pdf_reporte(contexto: ReporteJugadorContexto, plantilla: str = "reporte_jugador.html") -> bytes:
    """Genera un PDF en memoria a partir del contexto del reporte.

    Esta función NO sabe nada de Streamlit ni de cómo se obtienen los datos.
    Solo recibe un contexto ya preparado, renderiza la plantilla HTML y lo
    convierte a PDF usando WeasyPrint.

    Parameters
    ----------
    contexto : ReporteJugadorContexto
        Datos ya preparados para el reporte.
    plantilla : str
        Nombre del archivo de plantilla HTML dentro de la carpeta `templates`.

    Returns
    -------
    bytes
        Contenido del PDF listo para ser enviado al navegador o guardado en disco.
    """

    if HTML is None:
        raise RuntimeError(
            "La librería 'weasyprint' no está instalada. Instálala con 'pip install weasyprint' para habilitar la exportación a PDF."
        )

    html_str = renderizar_html_reporte(contexto, plantilla=plantilla)
    pdf_bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes


def _fig_to_data_uri(fig) -> str:

    img_bytes = fig.to_image(format="png")
    b64 = base64.b64encode(img_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def construir_contexto_reporte_perfil(
    df,
    datos_jugador,
    jugador: str,
    categoria: str,
    seccion: str,
    vista: str,
    fecha: str,
) -> ReporteJugadorContexto:

    # Preparar datos base en formato dict para poder modificarlos según la vista
    if hasattr(datos_jugador, "to_dict"):
        datos_dict = datos_jugador.to_dict()
    else:
        datos_dict = dict(datos_jugador)

    # Definir columnas principales de fuerza y movilidad
    columnas_fuerza = [
        "CUAD DER (N)",
        "CUAD IZQ (N)",
        "WOLLIN DER",
        "WOLLIN IZQ",
        "F PICO DER (IMTP) (N)",
        "F PICO IZQ (IMTP) (N)",
        "FP DER (CMJ) (N)",
        "FP IZQ (CMJ) (N)",
        "FF DER (CMJ) (N)",
        "FF IZQ (CMJ) (N)",
        "TRIPLE SALTO DER",
        "TRIPLE SALTO IZQ",
        "F PICO (IMTP) (N)",
        "FP (CMJ) (N)",
        "FF (CMJ) (N)",
    ]

    columnas_movilidad = [
        "AKE DER",
        "AKE IZQ",
        "THOMAS DER",
        "THOMAS IZQ",
        "LUNGE DER",
        "LUNGE IZQ",
    ]

    # Si estamos en PERFIL DEL GRUPO, usar componentes específicos de grupo
    if vista == "Perfil del Grupo" and seccion == "Fuerza":
        componentes = obtener_componentes_perfil_fuerza_grupal(df, categoria)
    elif vista == "Perfil del Grupo" and seccion == "Movilidad":
        componentes = obtener_componentes_perfil_movilidad_grupal(df, categoria)
    else:
        # Para las vistas basadas en jugador (Perfil del Jugador, Comparación), mantenemos la lógica individual
        pass

        # Validación básica de datos para evitar PDFs "vacíos" en Fuerza
        if seccion == "Fuerza":
            valores_validos = []
            for col in columnas_fuerza:
                if col in datos_dict:
                    valor = datos_dict[col]
                    try:
                        valor_float = float(valor)
                    except (TypeError, ValueError):
                        continue
                    if valor_float != 0.0:
                        valores_validos.append(valor_float)
            if not valores_validos:
                raise ValueError(
                    "Sin datos de fuerza válidos para este jugador. Verifica que las métricas de fuerza estén cargadas antes de exportar el PDF."
                )

            componentes = obtener_componentes_perfil_fuerza(df, datos_dict, jugador, categoria)
        elif seccion == "Movilidad":
            componentes = obtener_componentes_perfil_movilidad(df, datos_dict, jugador, categoria)
        else:
            raise ValueError(f"Sección no soportada para reporte PDF: {seccion}")

    figuras = componentes.get("figuras", [])
    tablas = componentes.get("tablas", {})

    graficos_paths = [_fig_to_data_uri(fig) for fig in figuras]

    tablas_html: List[str] = []

    # Seleccionar qué tablas incluir según la vista/sección
    if vista == "Perfil del Grupo" and seccion in ("Fuerza", "Movilidad"):
        keys_tablas = ["comparativa_grupal"]
    else:
        keys_tablas = ["zscores", "comparativa"]

    for key in keys_tablas:
        df_tabla = tablas.get(key)
        if df_tabla is not None and not df_tabla.empty:
            tablas_html.append(df_tabla.to_html(classes="tabla-metrica", border=0))

    contexto = ReporteJugadorContexto(
        nombre_jugador=jugador,
        categoria=categoria,
        fecha=fecha,
        seccion=seccion,
        vista=vista,
        graficos_paths=graficos_paths,
        tablas_html=tablas_html,
    )
    return contexto
