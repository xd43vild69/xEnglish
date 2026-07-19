# xEnglish — App Android (Kotlin + Compose)

Cliente push-to-talk: graba una frase, la envia al backend y muestra la correccion,
la version nativa y la explicacion. Reproduce el audio corregido bajo demanda.

## Abrir
1. Abre la carpeta `android/` en **Android Studio** (Ladybug+).
2. Genera el wrapper si falta el jar:  `gradle wrapper` (o usa el de Android Studio).
3. Sync Gradle y ejecuta en un emulador/dispositivo (minSdk 26).

## Configuracion del backend
- URL por defecto: `http://10.0.2.2:8000/` (el `localhost` del host desde el emulador).
  Para un dispositivo fisico usa la IP LAN de tu servidor Linux.
- La URL y la **API key** se guardan con DataStore (`AppConfig`). Añade una pantalla de
  ajustes o precargalas para probar. El interceptor de OkHttp inyecta `X-API-Key`.

## Estructura
- `audio/AudioRecorder.kt` — captura PCM 16 kHz mono y escribe WAV.
- `audio/AudioPlayer.kt` — reproduce el WAV corregido (Media3/ExoPlayer).
- `data/` — Retrofit API, DTOs (kotlinx.serialization), `PhraseRepository`, `AppConfig`.
- `di/AppModule.kt` — Hilt: OkHttp (+ API key), Retrofit, API.
- `ui/RecordViewModel.kt` + `ui/RecordScreen.kt` — estado y UI.

## TODO para pulir (fuera del esqueleto)
- Enganchar el boton al gesto press/release real (`pointerInput` + `detectTapGestures`).
- Pantalla de historial (usa `repository.history()`), pantalla de ajustes.
- Manejo de permiso denegado y estados de red offline.
