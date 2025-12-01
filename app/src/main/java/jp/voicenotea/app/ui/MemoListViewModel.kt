package jp.voicenotea.app.ui

import android.content.Context
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import jp.voicenotea.app.data.Memo
import jp.voicenotea.app.data.MemoDatabase
import jp.voicenotea.app.data.MemoRepositoryImpl
import jp.voicenotea.app.domain.SpeechRecognizerManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.Locale

private const val TAG = "MemoListViewModel"

sealed class RecordingState {
    object Idle : RecordingState()
    object Listening : RecordingState()
}

class MemoListViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(MemoListViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return MemoListViewModel(context) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}

class MemoListViewModel(context: Context) : ViewModel() {
    private val database = MemoDatabase.getDatabase(context)
    private val repository = MemoRepositoryImpl(database.memoDao())

    private val _continuousListeningEnabled = MutableStateFlow(false)
    private val _fullText = MutableStateFlow("")
    val fullText: StateFlow<String> = _fullText.asStateFlow()

    private val speechRecognizerManager = SpeechRecognizerManager(
        context,
        onPartialResult = { onPartialText(it) },
        onFinalResult = { onFinalText(it) },
        onError = { onError(it) },
        shouldContinueListening = { _continuousListeningEnabled.value }
    )

    val memos = repository.getAllMemos()

    private val _recordingState = MutableStateFlow<RecordingState>(RecordingState.Idle)
    val recordingState: StateFlow<RecordingState> = _recordingState.asStateFlow()

    val recognizedText = speechRecognizerManager.recognizedText
    val isListening = speechRecognizerManager.isListening
    val error = speechRecognizerManager.error

    private val _selectedMemoIds = MutableStateFlow<Set<Long>>(emptySet())
    val selectedMemoIds: StateFlow<Set<Long>> = _selectedMemoIds.asStateFlow()

    private val _isSelectionMode = MutableStateFlow(false)
    val isSelectionMode: StateFlow<Boolean> = _isSelectionMode.asStateFlow()

    private val _successMessage = MutableStateFlow<String?>(null)
    val successMessage: StateFlow<String?> = _successMessage.asStateFlow()

    fun startListening() {
        Log.d(TAG, "startListening called")
        _recordingState.value = RecordingState.Listening
        _continuousListeningEnabled.value = true
        _fullText.value = ""
        speechRecognizerManager.startListening(language = Locale.JAPAN)
    }

    fun stopListening() {
        Log.d(TAG, "stopListening called")
        _continuousListeningEnabled.value = false
        speechRecognizerManager.stopListening()
        _recordingState.value = RecordingState.Idle
        saveMemoFromTranscript(_fullText.value)
    }

    fun cancelListening() {
        Log.d(TAG, "cancelListening called")
        _continuousListeningEnabled.value = false
        speechRecognizerManager.cancel()
        _recordingState.value = RecordingState.Idle
        _fullText.value = ""
    }

    private fun onPartialText(text: String) {
        Log.d(TAG, "onPartialText: $text")
        // 部分的なテキストはUIに表示するが、保存はしない
    }

    private fun onFinalText(text: String) {
        Log.d(TAG, "onFinalText: $text")
        if (text.isBlank()) return

        // 前回の結果と結合
        _fullText.value = if (_fullText.value.isBlank()) {
            text
        } else {
            _fullText.value + "\n" + text
        }
        Log.d(TAG, "Updated fullText: ${_fullText.value}")
    }

    private fun onError(message: String) {
        Log.e(TAG, "onError: $message")
        // 連続リスニングが有効な場合は、エラーが発生しても実行中のままにする
        // 自動再開はSpeechRecognizerManager側で処理される
        if (!_continuousListeningEnabled.value) {
            _recordingState.value = RecordingState.Idle
        }
    }

    private fun saveMemoFromTranscript(transcript: String) {
        if (transcript.isBlank()) {
            Log.d(TAG, "Transcript is blank, not saving")
            _recordingState.value = RecordingState.Idle
            return
        }

        Log.d(TAG, "Saving memo from transcript: $transcript")
        viewModelScope.launch {
            try {
                val title = transcript.take(20).takeIf { it.isNotBlank() } ?: "Untitled Memo"
                val memo = Memo(
                    title = title,
                    body = transcript,
                    createdAt = System.currentTimeMillis(),
                    updatedAt = System.currentTimeMillis()
                )
                repository.insertMemo(memo)
                Log.d(TAG, "Memo saved successfully")
                _recordingState.value = RecordingState.Idle
            } catch (e: Exception) {
                Log.e(TAG, "Failed to save memo: ${e.message}")
                _recordingState.value = RecordingState.Idle
            }
        }
    }

    fun toggleMemoSelection(memoId: Long) {
        val currentSelection = _selectedMemoIds.value.toMutableSet()
        if (currentSelection.contains(memoId)) {
            currentSelection.remove(memoId)
        } else {
            currentSelection.add(memoId)
        }
        _selectedMemoIds.value = currentSelection

        // セレクションモードの終了判定
        if (currentSelection.isEmpty()) {
            _isSelectionMode.value = false
        } else if (currentSelection.isNotEmpty()) {
            _isSelectionMode.value = true
        }
    }

    fun clearSelection() {
        _selectedMemoIds.value = emptySet()
        _isSelectionMode.value = false
        _successMessage.value = null
    }

    private fun clearSelectionWithoutMessage() {
        _selectedMemoIds.value = emptySet()
        _isSelectionMode.value = false
    }

    fun clearSuccessMessage() {
        _successMessage.value = null
    }

    fun deleteSelectedMemos() {
        val selectedIds = _selectedMemoIds.value
        if (selectedIds.isEmpty()) return

        viewModelScope.launch {
            try {
                for (memoId in selectedIds) {
                    repository.deleteMemoById(memoId)
                }
                Log.d(TAG, "Successfully deleted ${selectedIds.size} memos")
                _successMessage.value = "${selectedIds.size}件のメモを削除しました"
                // トースト表示後に選択状態をクリア
                kotlinx.coroutines.delay(1500)
                clearSelectionWithoutMessage()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to delete memos: ${e.message}")
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        Log.d(TAG, "onCleared called")
        speechRecognizerManager.destroy()
    }
}
