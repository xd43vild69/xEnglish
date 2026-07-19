package com.xenglish.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class GrammarIssue(
    val error: String,
    val fix: String,
    val rule: String,
)

@Serializable
data class Explanation(
    @SerialName("grammar_issues") val grammarIssues: List<GrammarIssue> = emptyList(),
    @SerialName("native_note") val nativeNote: String = "",
    val tips: List<String> = emptyList(),
)

@Serializable
data class AnalyzeResponse(
    val id: String,
    @SerialName("created_at") val createdAt: String,
    val transcription: String,
    @SerialName("corrected_text") val correctedText: String,
    @SerialName("native_version") val nativeVersion: String,
    val explanation: Explanation,
    val language: String,
    @SerialName("audio_ready") val audioReady: Boolean,
    @SerialName("processing_ms") val processingMs: Map<String, Int> = emptyMap(),
)

@Serializable
data class PhraseListItem(
    val id: String,
    @SerialName("created_at") val createdAt: String,
    val transcription: String,
    @SerialName("corrected_text") val correctedText: String,
    @SerialName("audio_ready") val audioReady: Boolean,
)

@Serializable
data class PhraseListResponse(
    val items: List<PhraseListItem>,
    val total: Int,
)
