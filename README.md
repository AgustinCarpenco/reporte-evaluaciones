# Evaluación Física Integral – Atlético Colón

## Requisitos

- Python 3.10+ (recomendado)
- Archivo de datos `data/EVALUACIONES.xlsx`
- Imagen de escudo `data/escudo.png`

## Instalación

Desde la carpeta del proyecto (`/Users/agustin/reporte-evaluaciones`), se recomienda usar un entorno virtual para evitar conflictos con el Python del sistema (PEP 668 en macOS/Homebrew).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

Con el entorno virtual activado (`(.venv)` al inicio de la línea de la terminal), desde la carpeta del proyecto:

```bash
streamlit run app.py
```

La aplicación se abrirá en el navegador (habitualmente en `http://localhost:8501`).

## Estructura principal

- `app.py` – aplicación Streamlit principal.
- `modules/` – lógica de análisis (fuerza, movilidad, grupal, comparativo).
- `visualizations/` – gráficos Plotly.
- `utils/` – utilidades de datos, UI y generación de PDF.
- `config/settings.py` – rutas, colores, métricas y configuración de Plotly.

## Exportación a PDF

La exportación de reportes PDF utiliza:

- `weasyprint` para generar PDF a partir de HTML.
- Plantillas Jinja2 en la carpeta `templates/`.

Si `weasyprint` no está instalado, se lanzará un error claro indicando cómo instalarlo.
