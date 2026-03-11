# Corrección de Hilos para API y Sessión Streamlit (11 de Marzo de 2026)

## Cambio Realizado
Se ha modificado la forma en la que el hilo secundario (que corre el `TradingBot`) se comunica con la interfaz de Streamlit, moviendo la cola de mensajes a nivel de la sesión actual de la app (`st.session_state.global_q`) y atando el contexto de ejecución del bot al script con `add_script_run_ctx()`.

Adicionalmente, se corrigió el _warning_ visual generado por utilizar cajas de texto de Streamlit sin un título (label) definido ("label got an empty value").

## Razón del Cambio
En Python estándar (como lo ejecutaba `gui.py` con Tkinter), los hilos en segundo plano comparten toda la memoria del programa sin restricciones. Por el contrario, la arquitectura de Streamlit asigna un ambiente separado para cada usuario o cada recarga de página usando una tabla llamada "Execution Context".

Cuando la librería `iqoptionapi` generaba respuestas a través de tu Bot e intentaba ejecutar el `bot_callback`, los identificadores de sesión de Streamlit se perdían ("ScriptRunContext missing"). Esto causaba que Streamlit no supiera _a qué sesión_ de navegador pertenecía ese hilo, por lo que rompía con el error `st.session_state has no key "q"`. 

Al agregar la función `add_script_run_ctx` (provista internamente por la librería de Streamlit), le estamos "pegando" el identificador de la sesión actual al hilo del bot, para que sepa exactamente dónde entregar los mensajes.
