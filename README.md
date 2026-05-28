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