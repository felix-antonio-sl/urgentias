#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

# Variables (modifica según sea necesario)
APP_NAME="urgentias"
USER="fx"
GROUP="www-data"
APP_DIR="/home/$USER/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
DOMAIN="urgentias.com"
EMAIL="felixsanhueza@me.com"  # Para notificaciones del certificado SSL

# Actualizar e instalar paquetes necesarios
#sudo apt update
#sudo apt install -y python3-pip python3-venv nginx

# Navegar al directorio de la aplicación
#cd $APP_DIR

# Crear y activar el entorno virtual si no existe
#if [ ! -d "$VENV_DIR" ]; then
#    python3 -m venv $VENV_DIR
#fi

# Activar el entorno virtual
#source $VENV_DIR/bin/activate

# Actualizar pip e instalar Gunicorn
#pip install --upgrade pip
#pip install gunicorn

# Desactivar el entorno virtual
#deactivate

# Crear un archivo de servicio de systemd para Gunicorn
# sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
# [Unit]
# Description=Gunicorn instance to serve $APP_NAME
# After=network.target

# [Service]
# User=$USER
# Group=$GROUP
# WorkingDirectory=$APP_DIR
# Environment="PATH=$VENV_DIR/bin"
# ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$APP_DIR/$APP_NAME.sock manage:app

# [Install]
# WantedBy=multi-user.target
# EOF

# Iniciar y habilitar el servicio de Gunicorn
sudo systemctl daemon-reload
sudo systemctl start $APP_NAME
sudo systemctl enable $APP_NAME

# Configurar Nginx para hacer proxy a Gunicorn
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location /static/ {
        alias $APP_DIR/app/static/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$APP_NAME.sock;
    }
}
EOF

# Habilitar la configuración del bloque de servidor de Nginx
sudo ln -s /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled

# Eliminar la configuración predeterminada de Nginx
sudo rm /etc/nginx/sites-enabled/default

# Probar la configuración de Nginx
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx

# Ajustar el firewall (si se usa UFW)
sudo ufw allow 'Nginx Full'

# Opcional: Obtener certificados SSL usando Let's Encrypt (Certbot)
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $EMAIL

# Recargar Nginx para aplicar la configuración SSL
sudo systemctl reload nginx

echo "Despliegue completado. Tu aplicación debería estar accesible en https://$DOMAIN"
