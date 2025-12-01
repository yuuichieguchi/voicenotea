package jp.voicenotea.app.domain

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import java.util.Locale
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

private const val TAG = "SpeechRecognizerManager"
private const val CALLBACK_TIMEOUT_MS = 3000L

/**
 * セッションベースの音声認識マネージャー
 * 各音声認識セッションは一意のSessionIdで識別され、
 * 前のセッションとの状態汚染を防ぐ
 */
class SpeechRecognizerManager(
    context: Context,
    private val onPartialResult: (String) -> Unit = {},
    private val onFinalResult: (String) -> Unit = {},
    private val onError: (String) -> Unit = {},
    private val shouldContinueListening: () -> Boolean = { false }
) : RecognitionListener {

    private val recognizer: SpeechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
    private val handler = Handler(Looper.getMainLooper())

    // セッション管理
    private val activeSession: AtomicReference<RecognitionSession?> = AtomicReference(null)
    private val activeSessionId: AtomicReference<SessionId?> = AtomicReference(null)

    // イベントストリーム
    private val _sessionEvents = MutableSharedFlow<SessionEvent>(extraBufferCapacity = 64)
    val sessionEvents: SharedFlow<SessionEvent> = _sessionEvents.asSharedFlow()

    // UI向けの状態
    private val _recognizedText = MutableStateFlow("")
    val recognizedText: StateFlow<String> = _recognizedText.asStateFlow()

    private val _isListening = MutableStateFlow(false)
    val isListening: StateFlow<Boolean> = _isListening.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    // 内部フラグ
    private var isListeningFlag: Boolean = false

    init {
        recognizer.setRecognitionListener(this)
    }

    fun startListening(language: Locale = Locale.JAPAN) {
        if (isListeningFlag) {
            Log.d(TAG, "Already listening, ignoring start request")
            return
        }

        // 新しいセッションを作成
        val session = RecognitionSession()
        activeSession.set(session)
        activeSessionId.set(session.sessionId)
        session.clearText()
        session.isStopRequested = false
        _recognizedText.value = ""
        _error.value = null

        Log.d(TAG, "Starting new session: ${session.sessionId.value.take(8)}")

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "話してください…")
            putExtra("android.speech.extra.SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS", 10000)
        }

        try {
            recognizer.startListening(intent)
            isListeningFlag = true
            _isListening.value = true
            emitEvent(SessionEvent.SessionStarted(session.sessionId))
            Log.d(TAG, "Listening started for session: ${session.sessionId.value.take(8)}")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start listening: ${e.message}")
            activeSession.set(null)
            activeSessionId.set(null)
            _isListening.value = false
            emitEvent(SessionEvent.SessionError(
                session.sessionId,
                "音声認識を開始できませんでした",
                e
            ))
        }
    }

    fun stopListening() {
        val session = activeSession.get()
        if (session == null) {
            Log.d(TAG, "No active session to stop")
            return
        }

        Log.d(TAG, "Stopping session: ${session.sessionId.value.take(8)}")
        session.isStopRequested = true
        handler.removeCallbacksAndMessages(null)

        recognizer.stopListening()
        isListeningFlag = false
        _isListening.value = false

        // コールバックのタイムアウトを設定
        // onResults() が来ない場合でも3秒後に完了イベントを発行
        handler.postDelayed({
            completeSession(session)
        }, CALLBACK_TIMEOUT_MS)

        Log.d(TAG, "Waiting for final callback or timeout...")
    }

    fun cancelListening() {
        val session = activeSession.get()
        if (session == null) {
            Log.d(TAG, "No active session to cancel")
            return
        }

        Log.d(TAG, "Cancelling session: ${session.sessionId.value.take(8)}")
        session.isStopRequested = true
        handler.removeCallbacksAndMessages(null)
        recognizer.cancel()
        isListeningFlag = false
        _isListening.value = false
        _recognizedText.value = ""

        activeSessionId.set(null)
        activeSession.set(null)

        emitEvent(SessionEvent.SessionCancelled(session.sessionId))
    }

    fun destroy() {
        Log.d(TAG, "Destroying recognizer")
        handler.removeCallbacksAndMessages(null)
        recognizer.destroy()
    }

    // --- RecognitionListener 実装 ---

    override fun onReadyForSpeech(params: Bundle?) {
        val session = activeSession.get()
        if (session != null) {
            Log.d(TAG, "Ready for speech: ${session.sessionId.value.take(8)}")
        }
    }

    override fun onBeginningOfSpeech() {
        val session = activeSession.get()
        if (session != null) {
            Log.d(TAG, "Beginning of speech: ${session.sessionId.value.take(8)}")
        }
    }

    override fun onRmsChanged(rmsdB: Float) {
        // 音量メーター用
    }

    override fun onBufferReceived(buffer: ByteArray?) {}

    override fun onEndOfSpeech() {
        val session = activeSession.get()
        if (session != null) {
            Log.d(TAG, "End of speech: ${session.sessionId.value.take(8)}")
        }
    }

    override fun onError(error: Int) {
        val session = activeSession.get() ?: return
        val sessionId = activeSessionId.get() ?: return

        Log.d(TAG, "onError($error) for session: ${sessionId.value.take(8)}")

        isListeningFlag = false
        handler.removeCallbacksAndMessages(null)
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
        onError(errorMessage)
        _error.value = errorMessage

        if (session.getAccumulatedText().isNotEmpty()) {
            // テキストが蓄積されている場合は完了として扱う
            completeSession(session)
        } else {
            // テキストがない場合はエラーイベント
            emitEvent(SessionEvent.SessionError(sessionId, errorMessage))
            activeSession.set(null)
            activeSessionId.set(null)

            // リカバリー可能なエラーは再開を試みる
            if (isRecoverableError(error)) {
                restartIfNeeded()
            }
        }
    }

    override fun onResults(results: Bundle?) {
        val session = activeSession.get() ?: return
        val sessionId = activeSessionId.get() ?: return

        Log.d(TAG, "onResults for session: ${sessionId.value.take(8)}")

        isListeningFlag = false
        handler.removeCallbacksAndMessages(null)
        _isListening.value = false

        val texts = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        val text = texts?.firstOrNull().orEmpty()

        if (text.isNotEmpty()) {
            Log.d(TAG, "Recognized text: $text")
            session.appendText(text)
            _recognizedText.value = text
            emitEvent(SessionEvent.FinalResult(sessionId, text))
        }

        // セッション完了
        completeSession(session)
    }

    override fun onPartialResults(partialResults: Bundle?) {
        val session = activeSession.get() ?: return
        val sessionId = activeSessionId.get() ?: return

        val texts = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        val text = texts?.firstOrNull().orEmpty()

        if (text.isNotEmpty()) {
            Log.d(TAG, "Partial text: $text (session: ${sessionId.value.take(8)})")
            _recognizedText.value = text
            emitEvent(SessionEvent.PartialResult(sessionId, text))
            onPartialResult(text)
        }
    }

    override fun onEvent(eventType: Int, params: Bundle?) {}

    // --- Private helper functions ---

    private fun completeSession(session: RecognitionSession) {
        Log.d(TAG, "Completing session: ${session.sessionId.value.take(8)}")

        val finalText = session.getAccumulatedText()
        emitEvent(SessionEvent.SessionCompleted(session.sessionId, finalText))
        onFinalResult(finalText)

        // セッション終了後、連続リスニングが有効ならリスタート
        if (session.isStopRequested.not() && shouldContinueListening()) {
            restartIfNeeded()
        } else {
            activeSession.set(null)
            activeSessionId.set(null)
            _isListening.value = false
        }
    }

    private fun restartIfNeeded() {
        if (!shouldContinueListening()) {
            Log.d(TAG, "Continuous listening disabled, not restarting")
            activeSession.set(null)
            activeSessionId.set(null)
            return
        }

        Log.d(TAG, "Continuous listening enabled, scheduling restart")
        handler.postDelayed({
            if (!isListeningFlag && shouldContinueListening() && activeSession.get() == null) {
                Log.d(TAG, "Restarting listening")
                startListening()
            }
        }, 300L)
    }

    private fun isRecoverableError(error: Int): Boolean {
        return error in listOf(
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT,
            SpeechRecognizer.ERROR_NO_MATCH
        )
    }

    private fun emitEvent(event: SessionEvent) {
        try {
            if (!_sessionEvents.tryEmit(event)) {
                Log.w(TAG, "Failed to emit event: $event")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error emitting event: ${e.message}", e)
        }
    }
}
