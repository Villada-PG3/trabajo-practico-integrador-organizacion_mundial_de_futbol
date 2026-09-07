# Organización Mundial de Fútbol

Proyecto desarrollado con **Django** para gestionar la información de los mundiales de fútbol, incluyendo países participantes, jugadores, clubes, partidos y estadísticas.

## Requisitos

Antes de comenzar, asegurarse de tener instalado:

- Python 3.11 o superior
- Git
- pip (incluido con Python)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>
```

### 2. Crear y activar el entorno virtual

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias

Con el entorno virtual activado, ejecutar:

```bash
pip install -r requirements.txt
```

## Configuración de la base de datos

El proyecto utiliza **SQLite** como base de datos.

Aplicar las migraciones:

```bash
python manage.py migrate
```

Si se desea utilizar el panel de administración, crear un superusuario:

```bash
python manage.py createsuperuser
```

## Ejecutar la aplicación

Iniciar el servidor de desarrollo:

```bash
python manage.py runserver
```

Luego abrir el navegador en:

```
http://127.0.0.1:8000/
```

Panel de administración:

```
http://127.0.0.1:8000/admin/
```

## Estructura del proyecto

```text
.
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── proyecto/
└── mundial/
```

> Los nombres de las carpetas pueden variar según la estructura final del proyecto.

## Tecnologías utilizadas

- Python
- Django
- SQLite
- HTML
- Bootstrap 5