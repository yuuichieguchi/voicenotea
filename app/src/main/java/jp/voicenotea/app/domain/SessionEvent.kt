package jp.voicenotea.app.domain

/**
 * 音声認識セッションから ViewModel に発行されるイベント
 */
sealed class SessionEvent {
    abstract val sessionId: SessionId
    abstract val timestamp: Long

    /**
     * セッション開始イベント
     */
    data class SessionStarted(
        override val sessionId: SessionId,
        override val timestamp: Long = System.currentTimeMillis()
    ) : SessionEvent()

    /**
     * 部分的なテキスト認識結果
     * UI でリアルタイム表示用
     */
    data class PartialResult(
        override val sessionId: SessionId,
        val text: String,
        val confidence: Float = 0f,
        override val timestamp: Long = System.currentTimeMillis()
    ) : SessionEvent()

    /**
     * 最終的なテキスト認識結果
     * 単一の句や単語が完全に認識された
     */
    data class FinalResult(
        override val sessionId: SessionId,
        val text: String,
        override val timestamp: Long = System.currentTimeMillis()
    ) : SessionEvent()

    /**
     * セッションが正常に完了
     * 全ての認識コールバックが処理済み
     */
    data class SessionCompleted(
        override val sessionId: SessionId,
        val finalText: String,
        override val timestamp: Long = System.currentTimeMillis()
    ) : SessionEvent()

    /**
     * セッションがキャンセルされた
     */
    data class SessionCancelled(
        override val sessionId: SessionId,
        override val timestamp: Long = System.currentTimeMillis()
    ) : SessionEvent()

    /**
     * セッション中にエラーが発生
     */
    data class SessionError(
        override val sessionId: SessionId,
        val errorMessage: String,
        val exception: Exception? = null,
        override val timestamp: Long = System.currentTimeMillis()
    ) : SessionEvent()
}
