package com.xenglish.audio

import android.content.Context
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import java.io.File

/** Reproductor simple para el WAV corregido descargado del backend. */
class AudioPlayer(context: Context) {
    private val player = ExoPlayer.Builder(context).build()

    fun play(file: File) {
        player.setMediaItem(MediaItem.fromUri(file.toURI().toString()))
        player.prepare()
        player.playWhenReady = true
    }

    fun release() = player.release()
}
