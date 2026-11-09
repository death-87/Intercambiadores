# Actualizar el servicio de guardado

1. Antes de actualizar, descarga el respaldo JSON del visor. Si se reinicia, usa **Recuperar avance** en el mismo navegador.
2. En el proyecto de Google Apps Script asociado al guardado de **Diseño3D**, reemplaza el código del servicio (normalmente `Código.gs` o `Code.gs`) por el archivo completo `guardar_diseno.gs`. Debe quedar una sola función `doPost`, la de esta versión.
3. Ve a **Implementar → Administrar implementaciones → Editar → Nueva versión → Implementar**. Actualiza la implementación existente para conservar la URL que usa la aplicación y sus permisos de ejecución.
4. Reemplaza `pages/diseño.py` y `visor_3d/index.html` por sus versiones actualizadas.
5. Selecciona **1641**, recupera el borrador si corresponde, cambia el TAG a **C1641** y guarda. El servicio verifica C1641 antes de retirar las filas de 1641.

Las filas reemplazadas o retiradas quedan copiadas en **Respaldo_Diseño3D** dentro del mismo archivo de Sheets. No se elimina información de Hoja 1 ni de Datos Operacionales. La app solo confirma el renombrado cuando encuentra el diseño nuevo y el TAG anterior ya no está en Diseño3D.

Crear un equipo nuevo usando otro como plantilla conserva el equipo original; cambiar el TAG de un registro existente lo renombra.
