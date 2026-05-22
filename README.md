# Gestor de Gastos

Web app para registrar ingresos y gastos personales, con dashboard de gráficos y exportación a CSV/Excel.

## Funcionalidades

- Registro de ingresos y gastos con categorías
- Dashboard con gráficos de balance mensual
- Filtros por mes, año, tipo y categoría
- Exportación a CSV y Excel
- Login y registro de usuarios con contraseña encriptada

## Requisitos

- Python 3.8 o superior

## Instalación

**1. Clona el repositorio:**
```bash
git clone https://github.com/DavidPm2405/Gestor-Gastos.git
cd Gestor-Gastos
```

**2. Instala las dependencias:**
```bash
pip install -r requirements.txt
```

**3. Corre la app:**
```bash
python app.py
```

**4. Abre el navegador en:**
```
http://localhost:5000
```

**5. Regístrate con usuario y contraseña y listo.**

## Tecnologías usadas

- Python + Flask
- SQLite (base de datos local)
- Bootstrap 5 (diseño)
- Chart.js (gráficos)
- openpyxl (exportación a Excel)
