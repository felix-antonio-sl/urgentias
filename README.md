# Urgentias

Aplicación web para la gestión y documentación en tiempo real de atenciones en servicios de urgencias médicas. Urgentias permite registrar información clínica, manejar usuarios, procesar textos no estructurados, y documentar detalles de atención de manera estructurada, implementando principios de documentación en medicina de emergencia.

## Estructura del Proyecto

```plain
├── app/
│   ├── __init__.py             # Configuración inicial de la aplicación
│   ├── forms.py                # Formularios para la interfaz web
│   ├── models/               # Modelos de base de datos
│   ├── static/prompts/                # Plantillas de prompt para procesamiento de IA
│   ├── routes/                 # Rutas de la aplicación
│   ├── static/css/styles.css   # Estilos personalizados de la aplicación
│   ├── templates/              # Plantillas HTML
│   └── utils.py                # Funciones utilitarias de procesamiento de IA
├── config/
│   └── config.py               # Configuraciones de desarrollo y producción
├── manage.py                   # Comandos de administración de Flask
└── requirements.txt            # Dependencias de Python
```

## Configuración y Despliegue

Urgentias utiliza Flask para la lógica de backend, Gunicorn como servidor WSGI y Nginx como servidor proxy inverso. Los pasos básicos de configuración son los siguientes:

### 1. Configuración del Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuración de Gunicorn

Se configura Gunicorn para ejecutar la aplicación como un servicio de sistema.

Ejemplo de archivo `/etc/systemd/system/urgentias.service`:

```ini
[Unit]
Description=Gunicorn instance to serve Urgentias
After=network.target

[Service]
User=fx
Group=www-data
WorkingDirectory=/home/fx/urgentias
Environment="PATH=/home/fx/urgentias/venv/bin"
ExecStart=/home/fx/urgentias/venv/bin/gunicorn --workers 3 --bind unix:/home/fx/urgentias/urgentias.sock manage:app

[Install]
WantedBy=multi-user.target
```

Iniciar y habilitar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl start urgentias
sudo systemctl enable urgentias
```

### 3. Configuración de Nginx

Ejemplo de configuración en `/etc/nginx/sites-available/urgentias`:

```nginx
server {
    listen 80;
    server_name urgentias.com www.urgentias.com;

    location /static/ {
        alias /home/fx/urgentias/app/static/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/fx/urgentias/urgentias.sock;
    }
}
```

Habilitar la configuración en Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/urgentias /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Certificados SSL

Instalar Certbot para gestionar certificados SSL:

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

Obtener certificados:

```bash
sudo certbot --nginx -d urgentias.com -d www.urgentias.com
```

### 5. Variables de Entorno

Asegúrate de configurar las siguientes variables de entorno en el archivo `.env`:

- `SECRET_KEY`: Clave secreta para la aplicación Flask.
- `DATABASE_URL`: URL de la base de datos.
- `OPENAI_API_KEY`: Clave para la API de OpenAI.
- `ANTHROPIC_API_KEY`: Clave para la API de Anthropic.

## Funcionalidades Principales

1. **Gestión de Pacientes y Atenciones:** Manejo de información clínica, edad, y RUN.
2. **Procesamiento de Texto No Estructurado:** Extracción de datos médicos en JSON usando IA.
3. **Documentación de Historia y Atención en Emergencia:** Procesamiento incremental de detalles de atención, con énfasis en precisión y cronología.
4. **Asistente AI Integrado:** Generación automática de diagnóstico diferencial, manejo sugerido, próxima acción más importante y alertas de riesgos, utilizando inteligencia artificial.
5. **Autenticación de Usuarios:** Registro, inicio de sesión y seguridad CSRF.

## Configuración de Claves API

Asegúrate de configurar las siguientes variables de entorno en el archivo `.env`:

- `OPENAI_API_KEY`: Clave para la API de OpenAI utilizada por **ell**.
- `ANTHROPIC_API_KEY`: Clave para la API de Anthropic (si es aplicable).

## Consideraciones de Seguridad y Privacidad

- **Protección de Datos:** Los datos de los pacientes son sensibles. Asegúrate de que las comunicaciones con los servicios de AI cumplan con las normativas de protección de datos aplicables.
- **Manejo de Errores:** El sistema está diseñado para manejar de manera segura las interrupciones en los servicios de AI, notificando al usuario sin exponer información sensible.

## Dependencias

Consulta `requirements.txt` para una lista completa. Principales:

- `Flask`
- `SQLAlchemy`
- `Flask-Login`
- `WTForms`
- `Ell-AI` para procesamiento de prompts.

## Ejecutar la Aplicación Localmente

1. Activa el entorno virtual:

   ```bash
   source venv/bin/activate
   ```

2. Configura la base de datos:

   ```bash
   flask db upgrade
   ```

3. Inicia el servidor:

   ```bash
   flask run
   ```
