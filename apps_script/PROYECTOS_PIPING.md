# Guardar proyectos con nombre y abrirlos desde otros computadores

El guardado por nombre en el navegador está disponible sin configuración. Para sincronizar entre computadores, configura este servicio privado en Google Drive. No requiere cambiar el plan de Render ni contratar una base de datos.

1. Entra a https://script.google.com y crea un **proyecto nuevo**, distinto del servicio de Intercambiadores.
2. Copia el archivo completo `proyectos_piping.gs` en ese proyecto.
3. Ejecuta `configurarProyectosPiping` y autoriza el acceso a tu Drive. Crea la carpeta **Jndigital - Proyectos Piping**.
4. Copia el token que aparece en el registro de ejecución; no lo publiques en GitHub ni en el chat.
5. Ve a **Implementar → Nueva implementación → Aplicación web**. Ejecutar como **Yo**, acceso **Cualquier persona**. El token protege cada operación del servicio. Copia la dirección que termina en `/exec`.
6. En Streamlit Community Cloud, abre **Settings → Secrets** de la aplicación de desarrollo y agrega:

```toml
PIPING_PROJECTS_URL = "https://script.google.com/macros/s/TU_IMPLEMENTACION/exec"
PIPING_PROJECTS_TOKEN = "EL_TOKEN_DEL_REGISTRO"
PIPING_PROJECTS_PASSWORD = "UNA_CLAVE_PRIVADA_PARA_TUS_PROYECTOS"
```

La contraseña se usa en la aplicación antes de consultar o guardar proyectos. El token solo se envía desde el servidor; no se entrega al navegador. Conserva ambas claves en privado. La app de desarrollo continúa usando `desarrollo-jndigital`.

7. En Piping abre **Proyectos entre computadores**, introduce tu contraseña y pulsa **Entrar**. Ya podrás usar **Guardar en Google Drive** desde el cuadro Guardar proyecto y abrir desde la lista del servicio.

Cada proyecto conserva su nombre, equipos, diseños editables, posiciones, giros y piping. Se confirma el guardado solo después de verificar el archivo en Drive; las versiones anteriores no se eliminan. Si otro computador guardó una revisión más reciente, se rechaza la sobrescritura para evitar perder cambios. Usa otro nombre o abre la versión vigente.

El guardado local por nombre pertenece únicamente a ese navegador. Las descargas JSON continúan disponibles como respaldo adicional. Las cuentas Drive y la contraseña configuradas definen quién puede acceder a estos proyectos; la aplicación no los guarda en el repositorio de GitHub.
