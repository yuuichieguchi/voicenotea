package jp.voicenotea.app.domain

/**
 * 音声認識セッションのライフサイクルを表す状態
 */
enum class SessionState {
    /** アイドル状態（リッスン開始前） */
    IDLE,

    /** アクティブにリッスン中 */
    LISTENING,

    /** 結果処理中 */
    PROCESSING_RESULT,

    /** セッション完了 */
    COMPLETED,

    /** セッションキャンセル */
    CANCELLED,

    /** エラーで失敗 */
    FAILED;

    /**
     * 有効な状態遷移かを確認する
     */
    fun canTransitionTo(nextState: SessionState): Boolean {
        return when (this) {
            IDLE -> nextState == LISTENING
            LISTENING -> nextState in listOf(PROCESSING_RESULT, CANCELLED, FAILED)
            PROCESSING_RESULT -> nextState in listOf(COMPLETED, FAILED)
            COMPLETED -> nextState == LISTENING
            CANCELLED -> nextState == LISTENING
            FAILED -> nextState == LISTENING
        }
    }
}
