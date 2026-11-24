# Cuenta del propietario y almacenamiento de Piping

El modo invitado funciona sin iniciar sesión e incluye diseño, importación y descarga de JSON. El propietario puede abrir archivos desde «Cuenta de Piping · Mis diseños» y elegir «Sobrescribir archivo» o «Guardar como copia». Si el archivo cambió desde que se abrió, hay que volver a abrirlo o guardar una copia.

## Configuración del despliegue

1. En Cloudflare R2, crea una credencial S3 de lectura y escritura de objetos limitada al bucket privado `jndigital-piping`.
2. En Google Cloud, crea un cliente OAuth de tipo aplicación web. Registra como URI de redirección la dirección pública del despliegue directo con la ruta `/oauth2callback`. Usa el mismo origen para iniciar sesión. Streamlit devuelve al inicio de la app. Desde ahí, abre Piping otra vez.
3. En los Secrets del despliegue de Streamlit, incorpora estas secciones con valores reales. Conserva las otras configuraciones existentes. Usa un valor aleatorio fuerte para `cookie_secret`.

```toml
[auth]
redirect_uri = "https://DOMINIO_DEL_DESPLIEGUE/oauth2callback"
cookie_secret = "VALOR_ALEATORIO"
client_id = "CLIENTE_OAUTH"
client_secret = "SECRETO_OAUTH"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[piping_r2]
account_id = "ID_DE_LA_CUENTA_CLOUDFLARE"
bucket = "jndigital-piping"
access_key_id = "CLAVE_DE_ACCESO_R2"
secret_access_key = "SECRETO_R2"
owner_email = "CORREO_GOOGLE_DEL_PROPIETARIO"
```

Los valores reales van exclusivamente en Secrets. Streamlit requiere un despliegue directo para su flujo de autenticación. Comprueba que el dominio público enruta el callback al mismo despliegue antes de usarlo como origen de inicio de sesión.

## Verificación

1. En una ventana privada, diseña una línea, descarga el JSON e impórtalo nuevamente. Comprueba que el modo invitado no muestra la lista ni permite guardar en R2.
2. Inicia sesión con la cuenta configurada, vuelve a Piping y guarda un diseño de prueba. Desde otro navegador con la misma cuenta, abre la copia y comprueba su contenido.
3. Prueba una cuenta Google diferente. Debe quedar en modo invitado.
4. Si tienes proyectos en el servicio anterior de Google Drive, conserva su respaldo JSON y cárgalo en Piping para guardarlo en R2. La conexión no migra esos documentos automáticamente.
