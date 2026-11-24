# Piping y equipos en Jndigital

Desarrollo en la rama `desarrollo-jndigital`. Render continúa utilizando `codex/boquillas-sw`; los cambios de esta rama no se publican en el portal.

## Uso

1. Abre Piping e isométricos y crea una línea con tramos, codos, tees, reductores y válvulas.
2. En **Herramientas de equipo**, crea un intercambiador vertical u horizontal. También puedes abrir un respaldo JSON de Intercambiadores o editar un equipo que ya incorporaste.
3. Configura el modelo, dimensiones y boquillas con el editor existente. Pulsa **Usar este equipo en Piping** para incorporarlo al ensamblaje.
4. En **Ensamblaje de piping**, elige el extremo `TAG del equipo · boquilla` y agrega elementos. Entrada NPS y clase se heredan de la conexión; se agrega la brida contraparte donde corresponde.
Cada tramo, codo, tee o reductor permite elegir **Para soldar** o **Enflanchada** en su salida. La derivación de la tee se configura por separado. La entrada sigue el extremo elegido; para comenzar con una entrada enflanchada, agrega primero una brida WN. Las bridas de salida se agregan después del largo del cuerpo y se incluyen en el listado de materiales. Los botones **Continuar** y los extremos identificados del dibujo permiten elegir por dónde seguir; el botón de agregar indica la conexión de destino.

5. Para acoplar una línea existente, selecciona su primer elemento, elige una boquilla libre y pulsa **Acoplar seleccionado al extremo elegido**. Su continuación se mueve con ella. Elegir `Inicio de la línea` permite desacoplarla del equipo si ese extremo está libre.
6. Cambia X, Y, Z y giro del equipo para ubicarlo. Las líneas conectadas siguen sus boquillas. Los cambios de medidas y opciones de un componente seleccionado se aplican automáticamente; Deshacer permite recuperar el valor anterior.
7. Descarga el respaldo JSON del conjunto. PNG y PDF incluyen equipo y piping; el listado de materiales corresponde al piping.

La válvula de bola muestra cuerpo fundido partido, uniones apernadas, bridas de conexión, prensaestopa, vástago y palanca elevada con aro de mando según la referencia fotográfica.

Válvulas disponibles: compuerta, bola, globo, retención, mariposa, PSV y RV. PSV/RV tienen entrada y salida lateral con medida y clase independientes. El largo axial representa la altura de la válvula; el largo de derivación determina el tramo lateral hasta su salida. El giro define la orientación de esa salida. Los largos son configurables, no tablas de fabricante.

## Alcance

- Hasta seis equipos y 200 componentes por ensamblaje; respaldo de hasta 30 MB de contenido (archivos JSON importados hasta 32 MB), geometría por equipo hasta 16 MB.
- Conexiones de equipos: boquillas circulares enflanchadas libres, NPS 1/2 a 24 pulgadas, clases 150/300/600. No se habilitan extremos cerrados, rectangulares, cuadrados, conexiones roscadas ni la conexión especial de 42 pulgadas. El editor informa cuáles omite. Los equipos apilados se incorporan por separado.
- El equipo se exporta con su geometría visible real, sin texturas ni código ejecutable. Metros/Y vertical se convierten a milímetros/Z vertical. La geometría y el diseño editable se guardan dentro del JSON.
- Las boquillas reciben IDs persistentes al incorporarlas. Renombrarlas conserva la conexión. Si se elimina una boquilla conectada, la actualización del equipo se rechaza y se conserva el ensamblaje anterior.
- La unión es un árbol: un elemento continúa desde un solo extremo. No se cierran lazos ni se unen dos extremos ocupados.
- Este flujo usa respaldo local y descargas; no escribe equipos ni informes en Google Sheets.

## Verificación

`python -m unittest discover -s tests -p test_piping.py` verifica catálogo, materiales, PDF, herencia de conexiones de equipo y concordancia Python/JavaScript. `node tests/piping_equipment.mjs` verifica transformaciones, PSV con clases distintas, orden de conexiones, movimiento y rechazo de ciclos y boquillas inexistentes.

## Derivaciones sobre líneas y codos

- **Sockolet · SW:** se suelda sobre un tramo recto. Selecciona la línea principal, NPS de salida, posición desde el inicio del tramo, altura y giro. Por ejemplo, una principal de 6 pulgadas y salida de 2 genera un sockolet 6 × 2. Su salida permite continuar con piping y válvulas.
- **Thredolet · NPT:** montaje soldado sobre un tramo recto y salida roscada NPT. Se identifica como roscada y se representa en el dibujo. Permite continuar con un niple NPT macho y luego con válvulas roscadas NPT hembra. El editor rechaza uniones incompatibles.
- **Latrolet · 45°:** se monta en un tramo recto y genera una salida inclinada a 45° respecto de la línea principal. Posición, diámetro y giro son configurables.
- **Elbolet:** selecciona un codo existente. El accesorio se ubica en el centro de su recorrido. El selector permite orientar la derivación paralela a la recta de entrada o salida del codo, apuntar a +X, −X, +Y, −Y, +Z o −Z globales, o usar Giro libre. En Giro libre se ajustan el giro horizontal alrededor de Z y la elevación entre −90° y +90°. El piping conectado sigue la dirección elegida. Las direcciones de entrada y salida siguen los ejes reales del codo; los ejes globales permanecen como referencia del ensamblaje.

Se pueden colocar varias derivaciones en un mismo tramo. La línea principal conserva su continuidad y su extremo libre. Las derivaciones y sus continuaciones siguen la posición del tramo o codo; una posición fuera del tramo o una salida mayor que la principal se rechaza. Las alturas y la geometría de los accesorios son configurables; no constituyen tablas de fabricante ni un cálculo de refuerzo.

Selecciona un tramo o codo y utiliza **Agregar derivación sobre este tramo** o **Agregar derivación al centro del codo**, o elige el accesorio en la lista de elementos. Las salidas creadas aparecen entre los extremos de continuación.

Para desplazar el conjunto, mantén presionado el botón central de la rueda y arrastra. Girar la rueda mantiene el zoom; el botón izquierdo gira la vista y el derecho también desplaza.

Los diseños anteriores que identificaban como `latrolet` una conexión sobre un codo se convierten automáticamente a `elbolet`, conservando sus IDs, dirección y continuaciones. Los nuevos elbolets se eligen sobre codos de 90°; los diseños anteriores con codos de 45° siguen siendo legibles.

El elbolet se dibuja hueco, con una base recortada que asienta sobre la superficie curva del codo. La posición del asiento se calcula contra esa curva; el cordón sigue su perímetro y la boca de salida comparte eje con el piping de continuación. La representación del codo abre el paso bajo la derivación.

PSV y RV también tienen accesos directos en la lista de elementos. Mantienen entrada y salida enflanchadas independientes, resorte visible, vástago, columnas y palanca lateral.

## Las tres bocas de una tee

La tee identifica sus bocas como **lado A**, **lado B** y **derivación**. Si es el primer componente del dibujo, sus tres bocas quedan disponibles para continuar, incluso hacia atrás desde el lado A. Al incorporarla a una línea, el selector de entrada permite unirla por A, por B o por la derivación; esa boca queda ocupada y las otras dos disponibles. El panel muestra siempre sus tres bocas e indica las ocupadas.

Para entrar por la derivación de una tee reducida, la medida de entrada se hereda de la línea y se elige aparte la medida principal de A/B. Por ejemplo, una línea de 2 pulgadas puede entrar por la derivación de una tee 6 × 2; ambos lados rectos continúan con 6 pulgadas. Los largos y las terminaciones de los dos extremos libres conservan su edición automática. Los diseños anteriores usan entrada por A de forma predeterminada.

## Editar un equipo incorporado

Selecciona el equipo en el dibujo o en la lista del ensamblaje y pulsa **Editar forma y componentes**. Se abre **Herramientas de equipo** con el diseño editable de ese mismo equipo. También puedes elegir otro equipo desde el selector de nameplate / TAG, visible en esa sección. El encabezado indica cuál estás editando.

Al pulsar **Usar este equipo en Piping**, se actualiza el equipo existente: mantiene X, Y, Z, giro e identidad, y el piping conectado acompaña a sus boquillas. Si eliminas una boquilla con una línea conectada, la actualización se rechaza y el ensamblaje anterior se conserva; primero hay que desacoplar esa línea. El nameplate se muestra sobre el cuerpo y sigue la posición configurada en el editor; los respaldos anteriores reciben una placa visible a partir del TAG.

## Apoyo inferior de un equipo vertical

En el modelo J (vertical), **Extremo inferior → Faldón recto · continuación del shell hasta el piso** reemplaza el cierre inferior por un faldón cilíndrico soldado, del mismo diámetro que el shell y con borde inferior plano. Su altura se configura por separado entre 0,20 y 5 m. No lleva bonete, channel ni bridas inferiores. El extremo superior conserva su configuración y las boquillas existentes mantienen su identidad. La opción se guarda en el JSON y se exporta con el equipo al ensamblaje de piping.

## Niples y válvulas roscadas

Los tramos rectos pueden representar niples con entrada para soldar, NPT macho o inferida del extremo elegido, y salida para soldar, enflanchada o NPT macho. Para un niple roscado en ambos extremos, selecciona entrada NPT (o conecta desde una boca NPT hembra) y salida NPT. Las válvulas, incluidas PSV y RV, permiten elegir conexiones enflanchadas o NPT hembra en entrada y salida. Las medidas de salida de PSV/RV siguen siendo independientes.

Ejemplo: thredolet NPT hembra → niple NPT macho/macho → RV NPT hembra → niple de la medida de salida. Las uniones roscadas no agregan bridas; se representan las roscas y el listado distingue niples roscados y válvulas NPT. No se unen directamente macho con macho o hembra con hembra ni una boca roscada con una terminación soldada. Para continuar desde una boca macho se requiere una válvula hembra u otra unión compatible.

## Guardar proyectos por nombre

El botón **Guardar proyecto** abre un cuadro para escribir un nombre, por ejemplo **Equipo piping**. **Guardar en este navegador** conserva el conjunto completo en una biblioteca IndexedDB, sin descargar JSON. **Mis proyectos → Abrir seleccionado** recupera esa copia, incluso después de cerrar y volver a abrir la página en el mismo navegador. Esta biblioteca local no se sincroniza con otros computadores.

Para continuar desde otros lugares se requiere activar el servicio de Google Drive descrito en [PROYECTOS_PIPING.md](../apps_script/PROYECTOS_PIPING.md). El servicio es independiente del guardado de Intercambiadores. Una vez configurado, entra con la contraseña en **Proyectos entre computadores**, utiliza **Guardar en Google Drive** y abre el conjunto desde la lista del servicio. El cliente no anuncia un guardado remoto hasta recibir la verificación del servidor. Los cambios posteriores a la solicitud se identifican como pendientes. El servicio conserva versiones y rechaza sobrescrituras de una revisión antigua.

Las descargas e importaciones JSON quedan como respaldo opcional. En Herramientas de equipo, primero incorpora los cambios con **Usar este equipo en Piping** y después guarda el proyecto completo.

## Cambio inmediato del tipo de válvula

Al cambiar una válvula existente de enflanchada a roscada o viceversa, se actualiza el conjunto en una sola operación: se ajustan las terminaciones de los niples vecinos o se intercalan los niples necesarios cuando la conexión proviene de una brida u otro accesorio. Se conserva la medida del extremo y la continuación conectada. Los niples agregados aparecen en el dibujo y el listado de materiales; **Deshacer** recupera todo el cambio.

## Refuerzos, parches y marcas de inspección

En **Reparaciones / refuerzos**, elige un tramo recto y registra **Camisa Tipo B · soldada** o **Parche soldado**. Configura TAG, inicio desde el comienzo del tramo, largo, espesor, giro y comentario. Tipo B envuelve toda la circunferencia y muestra soldaduras longitudinales y de extremos; el parche muestra el sector angular elegido. La reparación debe quedar dentro del tramo. Usa **Nueva reparación** para agregar otra, o selecciónala en la lista para editarla automáticamente. Su diámetro sigue el del tramo.

En **Marcas y comentarios**, pulsa **Elegir punto para nueva marca**, escribe número / comentario y haz clic sobre una superficie del dibujo. La marca puede ser flecha con círculo, flecha o círculo; permite cambiar color y desplazamiento del comentario. El punto se vincula al componente o equipo elegido y acompaña su ubicación. Selecciona una marca de la lista para editar o eliminarla. El texto largo se conserva completo y figura en la leyenda del PDF.

Las reparaciones y marcas se guardan dentro del mismo proyecto, tanto en Mis proyectos como en JSON o Google Drive configurado. PNG y PDF incluyen las marcas visibles; el PDF agrega tablas con las reparaciones y referencias completas. Las reparaciones también aparecen en materiales. Al eliminar un componente se eliminan sus reparaciones y marcas; Deshacer recupera el conjunto. La representación no realiza cálculo estructural del refuerzo ni clasificación normativa de una ejecución real.


## Dirección, curvas y soldaduras de tramos

- El encabezado ámbar **Editar seleccionado** aplica los cambios al componente existente. El verde **Configurar próximo componente** prepara un elemento nuevo; indica el extremo elegido. Elegir otra salida cambia al modo de creación.
- **Dirección y curvatura del tramo** permite giro horizontal, inclinación vertical y curvatura continua sin insertar fittings. Los ángulos de dirección son relativos a la llegada; los componentes posteriores acompañan el cambio. El largo del tubo se mide sobre su eje desarrollado. Curvatura 0 mantiene una recta.
- **Posición del inicio libre** permite trasladar X/Y/Z del primer tubo y su continuación. Los componentes unidos a otro extremo conservan la posición de esa conexión. El inicio del primer tubo está disponible para prolongar hacia atrás, salvo que esté ocupado.
- **Elegir punto de soldadura en el dibujo** activa un clic sobre la superficie de un tubo. Lo divide sin desplazar su salida: `P01-01`, `P01-02` y cordón `W001`. Se puede repetir la división para generar más segmentos y soldaduras. Deshacer revierte la operación completa.
- Las derivaciones, marcas y reparaciones se reasignan al segmento correspondiente. Si el punto atraviesa una reparación, se pide elegir otro punto. Cada segmento debe conservar al menos 10 mm.
- Orientación, curvatura, posición, segmentos y cordones se incluyen en el proyecto guardado; las identificaciones se muestran en el dibujo y su captura. El modelo representa geometría y no verifica esfuerzos ni la ejecución de una unión inclinada.

### Eliminar un cordón

En **Soldaduras y división en segmentos**, selecciona el cordón por su nomenclatura (también puedes hacer clic sobre su anillo en el dibujo):

- **Eliminar cordón y unir tramos** recupera un solo tubo si los dos segmentos mantienen un recorrido continuo compatible. Conserva conexiones posteriores, derivaciones, marcas y reparaciones, y actualiza los TAG de los segmentos restantes.
- **Quitar solo cordón · conservar tramos** elimina el anillo y su identificación manteniendo las piezas independientes, incluso si cambiaste sus inclinaciones o curvaturas.

Ambas acciones se guardan en el proyecto y admiten **Deshacer / Rehacer**. Si los segmentos tienen formas distintas, el intento de unión conserva el proyecto y muestra la alternativa de quitar solo el cordón.


## Reducciones concéntricas y excéntricas para soldar

El catálogo ofrece **Reducción concéntrica BW** y **Reducción excéntrica BW** directamente. Comparten el tipo `reducer` para mantener compatibles los proyectos anteriores. Las fotos de referencia representan accesorios BW (butt weld, soldadura a tope); WN corresponde a la brida welding neck que ya tiene su propia opción.

Configura el diámetro de salida y el largo. La entrada hereda el NPS de la línea; la siguiente pieza hereda el NPS reducido. La excéntrica mantiene una generatriz plana: **Giro** permite orientarla arriba, abajo o lateralmente. El cambio de tipo se aplica inmediatamente al componente seleccionado. El perfil incluye cuellos rectos, transición suave, interior hueco y bordes de extremo; es una representación geométrica editable, no una tabla dimensional certificada. Los dos tipos quedan diferenciados en el listado de componentes y en los materiales exportados.
