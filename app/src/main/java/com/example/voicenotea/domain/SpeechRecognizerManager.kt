package com.example.voicenotea.domain

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import java.util.Locale
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

private const val TAG = "SpeechRecognizerManager"

class SpeechRecognizerManager(
    context: Context,
    private val onPartialResult: (String) -> Unit = {},
    private val onFinalResult: (String) -> Unit = {},
    private val onError: (String) -> Unit = {}
) : RecognitionListener {

    private val recognizer: SpeechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)

    private val _recognizedText = MutableStateFlow("")
    val recognizedText: StateFlow<String> = _recognizedText.asStateFlow()

    private val _isListening = MutableStateFlow(false)
    val isListening: StateFlow<Boolean> = _isListening.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    private var isListeningFlag: Boolean = false

    init {
        recognizer.setRecognitionListener(this)
    }

    fun startListening(
        language: Locale = Locale.JAPAN,
        onComplete: (String) -> Unit = {}
    ) {
        if (isListeningFlag) return

        Log.d(TAG, "Starting listening with language: $language")
        _error.value = null

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "話してください…")
        }

        try {
            recognizer.startListening(intent)
            isListeningFlag = true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start listening: ${e.message}")
            _error.value = "音声認識を開始できませんでした"
        }
    }

    fun stopListening() {
        if (!isListeningFlag) return
        Log.d(TAG, "Stopping listening")
        recognizer.stopListening()
        isListeningFlag = false
    }

    fun cancel() {
        Log.d(TAG, "Canceling listening")
        recognizer.cancel()
        isListeningFlag = false
        _isListening.value = false
        _recognizedText.value = ""
        _error.value = null
    }

    fun destroy() {
        Log.d(TAG, "Destroying recognizer")
        recognizer.destroy()
    }

    // --- RecognitionListener 実装 ---

    override fun onReadyForSpeech(params: Bundle?) {
        Log.d(TAG, "onReadyForSpeech")
        _isListening.value = true
        _error.value = null
    }

    override fun onBeginningOfSpeech() {
        Log.d(TAG, "onBeginningOfSpeech")
    }

    override fun onRmsChanged(rmsdB: Float) {
        // 音量メーター用
    }

    override fun onBufferReceived(buffer: ByteArray?) {}

    override fun onEndOfSpeech() {
        Log.d(TAG, "onEndOfSpeech")
    }

    override fun onError(error: Int) {
        isListeningFlag = false
        _isListening.value = false
        val errorMessage = when (error) {
            SpeechRecognizer.ERROR_AUDIO -> "音声入力エラー"
            SpeechRecognizer.ERROR_CLIENT -> "音声認識に失敗しました"
            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "マイク許可が必要です"
            SpeechRecognizer.ERROR_NETWORK -> "ネットワークエラー"
            SpeechRecognizer.ERROR_NO_MATCH -> "音声が認識されませんでした"
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "音声がありません"
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "ネットワークタイムアウト"
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "音声認識エンジンが利用できません"
            else -> "エラーが発生しました"
        }
        Log.e(TAG, "Speech recognizer error: $error - $errorMessage")
        _error.value = errorMessage
        onError(errorMessage)
    }

    override fun onResults(results: Bundle?) {
        isListeningFlag = false
        _isListening.value = false
        Log.d(TAG, "onResults")
        val texts = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        val text = texts?.firstOrNull().orEmpty()
        Log.d(TAG, "Recognized text: $text")
        _recognizedText.value = text
        onFinalResult(text)
    }

    override fun onPartialResults(partialResults: Bundle?) {
        Log.d(TAG, "onPartialResults")
        val texts = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        val text = texts?.firstOrNull().orEmpty()
        if (text.isNotEmpty()) {
            Log.d(TAG, "Partial text: $text")
            _recognizedText.value = text
            onPartialResult(text)
        }
    }

    override fun onEvent(eventType: Int, params: Bundle?) {}
}
