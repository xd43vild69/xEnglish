package com.xenglish.data

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PhraseRepository @Inject constructor(
    private val api: XEnglishApi,
) {
    /** Sube el WAV grabado y devuelve el analisis textual. */
    suspend fun analyze(wavFile: File): AnalyzeResponse {
        val body = wavFile.asRequestBody("audio/wav".toMediaType())
        val part = MultipartBody.Part.createFormData("audio", wavFile.name, body)
        val format = "wav".toRequestBody("text/plain".toMediaType())
        return api.analyze(part, format)
    }

    suspend fun history(limit: Int = 20, offset: Int = 0): PhraseListResponse =
        api.listPhrases(limit, offset)

    suspend fun detail(id: String): AnalyzeResponse = api.getPhrase(id)

    /** Descarga el WAV corregido a un archivo local para reproducirlo. */
    suspend fun downloadCorrectedAudio(id: String, dest: File, variant: String = "corrected"): File {
        val resp = api.getPhraseAudio(id, variant)
        resp.byteStream().use { input ->
            dest.outputStream().use { output -> input.copyTo(output) }
        }
        return dest
    }
}
