# 🚌 API Terminal de Ómnibus

Sistema backend desarrollado con **Django REST Framework** para la gestión de terminales, empresas de transporte, viajes, paradas y consultas de pasajeros 🚍

---

# 🚀 Tecnologías utilizadas

- 🐍 Python 3
- 🌐 Django
- ⚡ Django REST Framework
- 🐘 PostgreSQL
- 🔎 Django Filters
- 📄 drf-spectacular (Swagger/OpenAPI)
- ☁️ OpenWeather API
- 🗺️ OpenStreetMap Nominatim

# 🧠 Modelos principales
- Terminal
- Empresa
- Empleado
- Pasajero
- Viaje
- Parada
- Ubicacion

---

# ✨ Funcionalidades principales

✅ Gestión de terminales  
✅ Gestión de empresas de transporte  
✅ Gestión de viajes y paradas  
✅ Consulta de viajes por destino y día  
✅ Cálculo de horario estimado de llegada  
✅ Consulta de clima estimado en destino   

---

# 🔗 Endpoints de la API

La API expone los siguientes endpoints accesibles mediante HTTP y autenticación basada en JWT:

### 🔑 Autenticación (SimpleJWT)
- `POST /api/token/` - Obtención de tokens de acceso y actualización (JWT). Parámetros: `username`, `password`.
- `POST /api/token/refresh/` - Renovación del token de acceso expirado. Parámetros: `refresh`.

### 🏢 Terminales
- `GET /api/terminal/` - Listar todas las terminales físicas.
- `POST /api/terminal/` - Crear una nueva terminal (Solo **Superusuario**).
- `GET /api/terminal/{id}/` - Obtener información detallada de una terminal.
- `PUT/PATCH /api/terminal/{id}/` - Modificar datos de una terminal (Solo **Superusuario**).
- `DELETE /api/terminal/{id}/` - Eliminar una terminal (Solo **Superusuario**).

### 🏢 Empresas
- `GET /api/empresa/` - Listar y filtrar empresas de colectivos.
- `POST /api/empresa/` - Crear una nueva empresa (Solo **Superusuario**).
- `GET /api/empresa/{id}/` - Obtener detalles de una empresa.
- `PUT/PATCH /api/empresa/{id}/` - Modificar datos de una empresa (Solo **Superusuario**).
- `DELETE /api/empresa/{id}/` - Eliminar una empresa (Solo **Superusuario**).

### 👨‍💼 Empleados
- `GET /api/empleado/` - Listar empleados (los encargados ven los de su empresa; superusuarios ven todos).
- `POST /api/empleado/` - Registrar un nuevo empleado vinculándolo a un usuario base y asignando un rol (`ENCARGADO`, `VENTANILLA`). Si el emisor es Superusuario, debe indicar el ID de la `empresa`. Parámetros: `username`, `dni`, `password`, `first_name`, `last_name`, `rol`.
- `GET /api/empleado/{id}/` - Detalles de un empleado.
- `PUT/PATCH /api/empleado/{id}/` - Modificar datos de un empleado.
- `DELETE /api/empleado/{id}/` - Eliminar empleado (Solo **Encargado/Superusuario**).

### 👤 Pasajeros
- `POST /api/pasajero/` - Registrar públicamente un nuevo pasajero. Parámetros: `username`, `dni`, `password`, `telefono`, `first_name`, `last_name`.
- `GET /api/pasajero/` - Ver el perfil del pasajero autenticado.
- `PUT/PATCH /api/pasajero/{id}/` - Modificar perfil de pasajero.

### 📍 Ubicaciones
- `GET /api/ubicacion/` - Listar ubicaciones geográficas.
- `POST /api/ubicacion/` - Crear una ubicación (Solo **Empleado/Superusuario**). Valida automáticamente el nombre mediante **OpenStreetMap Nominatim** para obtener y sanitizar latitud y longitud oficiales. Parámetros: `nombre_oficial`.
- `GET /api/ubicacion/{id}/` - Detalles de una ubicación.

### 🗺️ Viajes y Recorridos
- `GET /api/viaje/` - Listar todos los viajes. Si el usuario es empleado, solo ve los pertenecientes a su empresa.
- `POST /api/viaje/` - Crear un nuevo viaje asociándolo automáticamente a la empresa del empleado creador.
- `GET /api/viaje/{id}/` - Detalles completos del viaje, incluyendo paradas ordenadas.
- `PUT/PATCH /api/viaje/{id}/` - Modificar un viaje (Solo **Empleado de la empresa/Superusuario**).
- `DELETE /api/viaje/{id}/` - Eliminar un viaje.
- **Acciones avanzadas:**
  - `GET /api/viaje/buscar_viajes/?destino={lugar}&dia={LUNES-DOMINGO}&terminal_id={uuid_opcional}` - Buscador inteligente. Realiza búsquedas accent-insensitive y parciales sobre los destinos de las paradas, calcula el horario estimado de llegada a esa parada sumando la duración y demoras actuales del día, y consulta a **OpenWeatherMap** para obtener el pronóstico climático estimado en el momento preciso de arribo. También ejecuta la evaluación del estado lazy para actualizar a `EN_VIAJE` o `FINALIZADO` según la hora actual.
  - `GET /api/viaje/pantalla_terminal/?terminal_id={uuid_opcional}` - Consulta de arribos y salidas programadas del día actual de una terminal en específico, ordenadas cronológicamente para la pantalla de información al público.
  - `POST /api/viaje/{id}/actualizar_estado_diario/` - Permite a los empleados registrar o actualizar las novedades operativas de un viaje para una fecha determinada. Parámetros en JSON: `estado` (`A_TIEMPO`, `EN_VIAJE`, `ABORDANDO`, `DEMORADO`, `FINALIZADO`, `CANCELADO`), `demora_minutos`, `motivo`, `fecha` (`YYYY-MM-DD`).

### 🛑 Paradas
- `GET /api/parada/` - Listar paradas intermedias de los recorridos.
- `POST /api/parada/` - Crear parada con orden, precio y tiempo transcurrido desde la salida.
- `PUT/PATCH /api/parada/{id}/` - Modificar parada.
- `DELETE /api/parada/{id}/` - Eliminar parada.

### 📅 Estados Diarios
- `GET /api/estado-diario/` - Listar todos los registros de novedades diarias de viajes.
- `POST /api/estado-diario/` - Crear un nuevo registro de estado diario.
- `GET/PUT/PATCH/DELETE /api/estado-diario/{id}/` - Administrar estados de días específicos.

---

# ⚙️ Instalación del proyecto

## 📥 1. Clonar repositorio

```bash
git clone https://github.com/Fantitom03/A-que-hora-viajo
cd A-que-hora-viajo
```

## 🐍 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate # En Linux/Mac
# o
venv\Scripts\activate     # En Windows
```

## 📦 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 🔐 Variables de entorno
#### Crear un archivo .env
```bash
DB_NAME=nombre_de_base_de_datos_pg
DB_USER=usuario_de_base_de_datos
DB_PASSWORD=contraseña_de_base_de_datos
DB_PORT=puerto_de_base_de_datos
SECRET_KEY=clave_secreta
DEBUG=True 
OPENWEATHER_API_KEY=api_key_OpenWeatherAPI
KEY_JWT=key_jwt
```

## 🗄️ Migraciones
```bash
python manage.py makemigrations 
python manage.py migrate
```

## ▶️ Ejecutar servidor
```bash
python manage.py runserver
```
Servidor disponible en:
http://127.0.0.1:8000/

---

## 📚 Swagger / Documentación API
### 🧾 Swagger UI
http://127.0.0.1:8000/api/docs/


### 📄 OpenAPI Schema
http://127.0.0.1:8000/api/schema/

---

## 🌐 Integración de APIs externas
### ☁️ OpenWeatherMap
Utilizada para obtener el pronóstico climático estimado según la hora de llegada del viaje.

### 🗺️ OpenStreetMap Nominatim
Utilizada para validar y normalizar ubicaciones ingresadas por el usuario.

# 👨‍💻 Autores
Proyecto académico realizado por **Centeno Joaquin** y **Leiva Francisco** para la materia Desarrollo de APIs - Ingeniería Informática - Facultad de Tecnología y Ciencias Aplicadas - Universidad Nacional de Catamarca