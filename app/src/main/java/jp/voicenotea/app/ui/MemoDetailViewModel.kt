package jp.voicenotea.app.ui

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import jp.voicenotea.app.data.Memo
import jp.voicenotea.app.data.MemoDatabase
import jp.voicenotea.app.data.MemoRepositoryImpl
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MemoDetailViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(MemoDetailViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return MemoDetailViewModel(context) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}

class MemoDetailViewModel(context: Context) : ViewModel() {
    private val database = MemoDatabase.getDatabase(context)
    private val repository = MemoRepositoryImpl(database.memoDao())

    private val _memo = MutableStateFlow<Memo?>(null)
    val memo: StateFlow<Memo?> = _memo.asStateFlow()

    private val _title = MutableStateFlow("")
    val title: StateFlow<String> = _title.asStateFlow()

    private val _body = MutableStateFlow("")
    val body: StateFlow<String> = _body.asStateFlow()

    private val _isSaving = MutableStateFlow(false)
    val isSaving: StateFlow<Boolean> = _isSaving.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    private val _successMessage = MutableStateFlow<String?>(null)
    val successMessage: StateFlow<String?> = _successMessage.asStateFlow()

    fun loadMemo(memoId: Long) {
        viewModelScope.launch {
            try {
                val loadedMemo = repository.getMemoById(memoId)
                if (loadedMemo != null) {
                    _memo.value = loadedMemo
                    _title.value = loadedMemo.title
                    _body.value = loadedMemo.body
                } else {
                    _errorMessage.value = "Memo not found"
                }
            } catch (e: Exception) {
                _errorMessage.value = "Failed to load memo: ${e.message}"
            }
        }
    }

    fun updateTitle(newTitle: String) {
        _title.value = newTitle
    }

    fun updateBody(newBody: String) {
        _body.value = newBody
    }

    fun saveMemo() {
        val currentMemo = _memo.value ?: return
        _isSaving.value = true

        viewModelScope.launch {
            try {
                val updatedMemo = currentMemo.copy(
                    title = _title.value,
                    body = _body.value,
                    updatedAt = System.currentTimeMillis()
                )
                repository.updateMemo(updatedMemo)
                _memo.value = updatedMemo
                _isSaving.value = false
                _successMessage.value = "メモを保存しました"
            } catch (e: Exception) {
                _isSaving.value = false
                _errorMessage.value = "Failed to save memo: ${e.message}"
            }
        }
    }

    fun deleteMemo() {
        val currentMemo = _memo.value ?: return
        viewModelScope.launch {
            try {
                repository.deleteMemoById(currentMemo.id)
                _memo.value = null
                _title.value = ""
                _body.value = ""
                _successMessage.value = "メモを削除しました"
            } catch (e: Exception) {
                _errorMessage.value = "Failed to delete memo: ${e.message}"
            }
        }
    }

    fun clearError() {
        _errorMessage.value = null
    }

    fun clearSuccess() {
        _successMessage.value = null
    }
}
