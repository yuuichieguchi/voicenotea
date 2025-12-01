package jp.voicenotea.app.domain

import java.util.UUID

/**
 * スレッドセーフな一意なセッション識別子
 * 各音声認識セッションに対して作成される
 */
@JvmInline
value class SessionId(val value: String) {
    companion object {
        fun generate(): SessionId = SessionId(UUID.randomUUID().toString())
    }

    override fun toString(): String = value
}
