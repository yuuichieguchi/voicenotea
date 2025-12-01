package jp.voicenotea.app.domain

import android.util.Log
import java.util.concurrent.atomic.AtomicReference

private const val TAG = "SessionStateMachine"

/**
 * セッションの状態遷移をスレッドセーフに管理する
 */
class SessionStateMachine {
    private val currentState: AtomicReference<SessionState> = AtomicReference(SessionState.IDLE)

    fun getState(): SessionState = currentState.get()

    /**
     * 指定の状態への遷移が可能かを確認する
     */
    fun canTransitionTo(nextState: SessionState): Boolean {
        val current = currentState.get()
        return current.canTransitionTo(nextState)
    }

    /**
     * 指定の状態への遷移を試みる
     * @throws IllegalStateException 無効な遷移の場合
     */
    fun transitionTo(nextState: SessionState) {
        val current = currentState.get()
        if (!current.canTransitionTo(nextState)) {
            val error = "Invalid state transition: $current → $nextState"
            Log.e(TAG, error)
            throw IllegalStateException(error)
        }

        val result = currentState.compareAndSet(current, nextState)
        if (result) {
            Log.d(TAG, "State transition: $current → $nextState")
        } else {
            // 競合が発生した場合は再試行
            Log.d(TAG, "State transition conflict, retrying...")
            transitionTo(nextState)
        }
    }

    /**
     * 状態をリセット（テスト用）
     */
    fun reset() {
        currentState.set(SessionState.IDLE)
    }
}
