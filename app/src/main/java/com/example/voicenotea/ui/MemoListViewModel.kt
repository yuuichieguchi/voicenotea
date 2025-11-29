package com.example.voicenotea.ui

import android.content.Context
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.voicenotea.data.Memo
import com.example.voicenotea.data.MemoDatabase
import com.example.voicenotea.data.MemoRepositoryImpl
import com.example.voicenotea.domain.SpeechRecognizerManager
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
    private val speechRecognizerManager = SpeechRecognizerManager(
        context,
        onPartialResult = { onPartialText(it) },
        onFinalResult = { onFinalText(it) },
        onError = { onError(it) }
    )

    val memos = repository.getAllMemos()

    private val _recordingState = MutableStateFlow<RecordingState>(RecordingState.Idle)
    val recordingState: StateFlow<RecordingState> = _recordingState.asStateFlow()

    val recognizedText = speechRecognizerManager.recognizedText
    val isListening = speechRecognizerManager.isListening
    val error = speechRecognizerManager.error

    fun startListening() {
        Log.d(TAG, "startListening called")
        _recordingState.value = RecordingState.Listening
        speechRecognizerManager.startListening(language = Locale.JAPAN)
    }

    fun stopListening() {
        Log.d(TAG, "stopListening called")
        speechRecognizerManager.stopListening()
        _recordingState.value = RecordingState.Idle
    }

    fun cancelListening() {
        Log.d(TAG, "cancelListening called")
        speechRecognizerManager.cancel()
        _recordingState.value = RecordingState.Idle
    }

    private fun onPartialText(text: String) {
        Log.d(TAG, "onPartialText: $text")
    }

    private fun onFinalText(text: String) {
        Log.d(TAG, "onFinalText: $text")
        saveMemoFromTranscript(text)
    }

    private fun onError(message: String) {
        Log.e(TAG, "onError: $message")
        _recordingState.value = RecordingState.Idle
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
                val title = transcript.take(50).takeIf { it.isNotBlank() } ?: "Untitled Memo"
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

    override fun onCleared() {
        super.onCleared()
        Log.d(TAG, "onCleared called")
        speechRecognizerManager.destroy()
    }
}
