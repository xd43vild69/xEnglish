package com.xenglish.ui

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xenglish.audio.AudioPlayer
import com.xenglish.audio.AudioRecorder
import com.xenglish.data.AnalyzeResponse
import com.xenglish.data.PhraseRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

sealed interface RecordUiState {
    data object Idle : RecordUiState
    data object Recording : RecordUiState
    data object Analyzing : RecordUiState
    data class Result(val data: AnalyzeResponse, val audioLoading: Boolean = false) : RecordUiState
    data class Error(val message: String) : RecordUiState
}

@HiltViewModel
class RecordViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val repository: PhraseRepository,
) : ViewModel() {

    private val recorder = AudioRecorder(context.cacheDir)
    private val player = AudioPlayer(context)

    private val _state = MutableStateFlow<RecordUiState>(RecordUiState.Idle)
    val state: StateFlow<RecordUiState> = _state.asStateFlow()

    fun startRecording() {
        recorder.start()
        _state.value = RecordUiState.Recording
    }

    fun stopAndAnalyze() {
        viewModelScope.launch {
            val wav = recorder.stopAsync() ?: run {
                _state.value = RecordUiState.Error("No se grabo audio")
                return@launch
            }
            _state.value = RecordUiState.Analyzing
            runCatching { repository.analyze(wav) }
                .onSuccess { _state.value = RecordUiState.Result(it) }
                .onFailure { _state.value = RecordUiState.Error(it.message ?: "Error de red") }
        }
    }

    /** Descarga (dispara el TTS) y reproduce el audio corregido. */
    fun playCorrected(variant: String = "corrected") {
        val current = _state.value as? RecordUiState.Result ?: return
        viewModelScope.launch {
            _state.value = current.copy(audioLoading = true)
            runCatching {
                val dest = File(context.cacheDir, "corrected_${current.data.id}.wav")
                repository.downloadCorrectedAudio(current.data.id, dest, variant)
            }.onSuccess {
                player.play(it)
                _state.value = current.copy(audioLoading = false)
            }.onFailure {
                _state.value = RecordUiState.Error(it.message ?: "No se pudo reproducir")
            }
        }
    }

    override fun onCleared() {
        player.release()
    }
}
