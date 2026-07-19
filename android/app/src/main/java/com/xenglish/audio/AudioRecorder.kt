package com.xenglish.audio

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Graba PCM 16 kHz mono 16-bit con AudioRecord y lo escribe como WAV.
 * Uso push-to-talk: start() al presionar, stop() al soltar.
 */
class AudioRecorder(private val cacheDir: File) {

    companion object {
        const val SAMPLE_RATE = 16000
        private const val CHANNEL = AudioFormat.CHANNEL_IN_MONO
        private const val ENCODING = AudioFormat.ENCODING_PCM_16BIT
    }

    @Volatile private var recording = false
    private var recordThread: Thread? = null
    private var outFile: File? = null

    @SuppressLint("MissingPermission")
    fun start(): File {
        val minBuf = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL, ENCODING)
        val bufSize = maxOf(minBuf, SAMPLE_RATE * 2) // ~1s
        val recorder = AudioRecord(
            MediaRecorder.AudioSource.MIC, SAMPLE_RATE, CHANNEL, ENCODING, bufSize,
        )
        val file = File(cacheDir, "rec_${System.currentTimeMillis()}.wav")
        outFile = file
        recording = true

        recordThread = Thread {
            RandomAccessFile(file, "rw").use { raf ->
                writeWavHeaderPlaceholder(raf)
                val buffer = ByteArray(bufSize)
                var totalBytes = 0
                recorder.startRecording()
                while (recording) {
                    val read = recorder.read(buffer, 0, buffer.size)
                    if (read > 0) {
                        raf.write(buffer, 0, read)
                        totalBytes += read
                    }
                }
                recorder.stop()
                recorder.release()
                patchWavHeader(raf, totalBytes)
            }
        }.also { it.start() }
        return file
    }

    /** Detiene y devuelve el WAV finalizado. */
    fun stop(): File? {
        recording = false
        recordThread?.join()
        recordThread = null
        return outFile
    }

    suspend fun stopAsync(): File? = withContext(Dispatchers.IO) { stop() }

    private fun writeWavHeaderPlaceholder(raf: RandomAccessFile) {
        raf.seek(0)
        raf.write(ByteArray(44)) // se rellena en patchWavHeader
    }

    private fun patchWavHeader(raf: RandomAccessFile, dataBytes: Int) {
        val byteRate = SAMPLE_RATE * 2
        val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
        header.put("RIFF".toByteArray())
        header.putInt(36 + dataBytes)
        header.put("WAVE".toByteArray())
        header.put("fmt ".toByteArray())
        header.putInt(16)            // subchunk1 size
        header.putShort(1)           // PCM
        header.putShort(1)           // mono
        header.putInt(SAMPLE_RATE)
        header.putInt(byteRate)
        header.putShort(2)           // block align
        header.putShort(16)          // bits per sample
        header.put("data".toByteArray())
        header.putInt(dataBytes)
        raf.seek(0)
        raf.write(header.array())
    }
}
