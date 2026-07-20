package com.xenglish.ui

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun RecordScreen(viewModel: RecordViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("xEnglish", style = MaterialTheme.typography.headlineMedium)
        Text(
            "Manten pulsado para grabar tu frase en ingles",
            style = MaterialTheme.typography.bodyMedium,
        )

        // Visual feedback state
        val isRecording = state is RecordUiState.Recording
        val scale by animateFloatAsState(
            targetValue = if (isRecording) 1.2f else 1.0f,
            label = "scale"
        )
        val buttonColor = if (isRecording) {
            MaterialTheme.colorScheme.error
        } else {
            MaterialTheme.colorScheme.primaryContainer
        }
        val iconColor = if (isRecording) {
            MaterialTheme.colorScheme.onError
        } else {
            MaterialTheme.colorScheme.onPrimaryContainer
        }

        // Boton push-to-talk interactivo
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .size(96.dp)
                .scale(scale)
                .clip(CircleShape)
                .background(buttonColor)
                .pointerInput(Unit) {
                    detectTapGestures(
                        onPress = {
                            try {
                                viewModel.startRecording()
                                awaitRelease()
                            } finally {
                                viewModel.stopAndAnalyze()
                            }
                        }
                    )
                }
        ) {
            Icon(
                imageVector = Icons.Filled.Mic,
                contentDescription = "Grabar (Mantener pulsado)",
                tint = iconColor,
                modifier = Modifier.size(48.dp)
            )
        }

        when (val s = state) {
            RecordUiState.Idle -> Unit
            RecordUiState.Recording -> Text("● Grabando...", color = MaterialTheme.colorScheme.error)
            RecordUiState.Analyzing -> CircularProgressIndicator()
            is RecordUiState.Error -> Text("Error: ${s.message}", color = MaterialTheme.colorScheme.error)
            is RecordUiState.Result -> ResultCard(s, viewModel)
        }
    }
}

@Composable
private fun ResultCard(s: RecordUiState.Result, viewModel: RecordViewModel) {
    val d = s.data
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            LabeledText("Escuchado", d.transcription)
            LabeledText("Corregido", d.correctedText)
            LabeledText("Version nativa", d.nativeVersion)

            if (d.explanation.grammarIssues.isNotEmpty()) {
                Text("Errores", fontWeight = FontWeight.Bold)
                d.explanation.grammarIssues.forEach {
                    Text("• \"${it.error}\" -> \"${it.fix}\"  (${it.rule})")
                }
            }
            if (d.explanation.nativeNote.isNotBlank()) {
                LabeledText("Nota", d.explanation.nativeNote)
            }
            d.explanation.tips.forEach { Text("💡 $it") }

            Button(onClick = { viewModel.playCorrected() }, enabled = !s.audioLoading) {
                if (s.audioLoading) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp))
                } else {
                    Icon(Icons.Filled.VolumeUp, contentDescription = null)
                    Text("  Escuchar pronunciacion")
                }
            }
        }
    }
}

@Composable
private fun LabeledText(label: String, value: String) {
    Column {
        Text(label, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
        Text(value, style = MaterialTheme.typography.bodyLarge)
    }
}
