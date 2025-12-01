package jp.voicenotea.app.domain

/**
 * 単一の音声認識セッションを表す
 * SessionId によって前のセッションと完全に隔離される
 */
data class RecognitionSession(
    val sessionId: SessionId = SessionId.generate(),
    val createdAt: Long = System.currentTimeMillis(),
    val stateMachine: SessionStateMachine = SessionStateMachine(),
    val textAccumulator: StringBuilder = StringBuilder(),
    var isStopRequested: Boolean = false
) {
    /**
     * 現在の蓄積テキストを取得
     */
    fun getAccumulatedText(): String = textAccumulator.toString()

    /**
     * テキストをバッファに追加
     * 複数の認識結果から集約される
     */
    fun appendText(text: String) {
        if (text.isBlank()) return
        if (textAccumulator.isNotEmpty()) {
            textAccumulator.append("\n")
        }
        textAccumulator.append(text)
    }

    /**
     * テキストバッファをクリア
     */
    fun clearText() {
        textAccumulator.clear()
    }

    /**
     * セッションをリセット（テスト用）
     */
    fun reset() {
        textAccumulator.clear()
        isStopRequested = false
        stateMachine.reset()
    }
}
