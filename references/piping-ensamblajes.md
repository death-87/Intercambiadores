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
- **Thredolet · NPT:** montaje soldado sobre un tramo recto y salida roscada NPT. Se identifica como roscada y se representa en el dibujo. Los componentes roscados de continuación quedan pendientes de la siguiente etapa; el editor impide conectarle por error un componente para soldar.
- **Latrolet · 45°:** se monta en un tramo recto y genera una salida inclinada a 45° respecto de la línea principal. Posición, diámetro y giro son configurables.
- **Elbolet:** selecciona un codo existente. El accesorio se ubica en el centro de su recorrido. El selector permite orientar la derivación paralela a la recta de entrada o a la recta de salida del codo. La dirección sigue esos ejes reales incluso al girar el codo o montar la línea vertical; no se calcula como un ángulo de 45° desde la tangente en el centro.

Se pueden colocar varias derivaciones en un mismo tramo. La línea principal conserva su continuidad y su extremo libre. Las derivaciones y sus continuaciones siguen la posición del tramo o codo; una posición fuera del tramo o una salida mayor que la principal se rechaza. Las alturas y la geometría de los accesorios son configurables; no constituyen tablas de fabricante ni un cálculo de refuerzo.

Selecciona un tramo o codo y utiliza **Agregar derivación sobre este tramo** o **Agregar derivación al centro del codo**, o elige el accesorio en la lista de elementos. Las salidas creadas aparecen entre los extremos de continuación.

Para desplazar el conjunto, mantén presionado el botón central de la rueda y arrastra. Girar la rueda mantiene el zoom; el botón izquierdo gira la vista y el derecho también desplaza.

Los diseños anteriores que identificaban como `latrolet` una conexión sobre un codo se convierten automáticamente a `elbolet`, conservando sus IDs, dirección y continuaciones. Los nuevos elbolets se eligen sobre codos de 90°; los diseños anteriores con codos de 45° siguen siendo legibles.
