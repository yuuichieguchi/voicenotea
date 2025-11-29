package com.example.voicenotea.ui.screens

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.example.voicenotea.R
import com.example.voicenotea.data.Memo
import com.example.voicenotea.ui.MemoListViewModel
import com.example.voicenotea.ui.RecordingState
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MemoListScreen(
    viewModel: MemoListViewModel,
    onMemoSelected: (Long) -> Unit
) {
    val memos = viewModel.memos.collectAsState(initial = emptyList())
    val recordingState = viewModel.recordingState.collectAsState()
    val isListening = viewModel.isListening.collectAsState()
    val error = viewModel.error.collectAsState()
    val recognizedText = viewModel.recognizedText.collectAsState()
    val isSelectionMode = viewModel.isSelectionMode.collectAsState()
    val selectedMemoIds = viewModel.selectedMemoIds.collectAsState()
    val successMessage = viewModel.successMessage.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val showDeleteConfirmDialog = remember { mutableStateOf(false) }

    LaunchedEffect(error.value) {
        error.value?.let { message ->
            snackbarHostState.showSnackbar(message)
        }
    }

    LaunchedEffect(successMessage.value) {
        successMessage.value?.let { message ->
            snackbarHostState.showSnackbar(message)
        }
    }

    Scaffold(
        topBar = {
            if (isSelectionMode.value) {
                TopAppBar(
                    title = { Text("${selectedMemoIds.value.size}件選択中") },
                    navigationIcon = {
                        IconButton(onClick = { viewModel.clearSelection() }) {
                            Icon(Icons.Default.Close, contentDescription = "キャンセル")
                        }
                    }
                )
            } else {
                TopAppBar(title = { Text(stringResource(R.string.app_name)) })
            }
        },
        floatingActionButton = {
            when {
                isSelectionMode.value -> {
                    FloatingActionButton(
                        onClick = { showDeleteConfirmDialog.value = true },
                        containerColor = MaterialTheme.colorScheme.error
                    ) {
                        Icon(Icons.Default.Delete, contentDescription = "選択削除")
                    }
                }
                recordingState.value == RecordingState.Idle -> {
                    FloatingActionButton(
                        onClick = { viewModel.startListening() }
                    ) {
                        Icon(Icons.Default.Mic, contentDescription = stringResource(R.string.start_recording))
                    }
                }
                recordingState.value == RecordingState.Listening -> {
                    FloatingActionButton(
                        onClick = { viewModel.stopListening() },
                        containerColor = MaterialTheme.colorScheme.error
                    ) {
                        Icon(Icons.Default.Close, contentDescription = stringResource(R.string.stop_recording))
                    }
                }
            }
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Listening status display
            if (isListening.value) {
                ListeningStatusBar(recognizedText.value)
            }

            // Memo list
            val memoList = memos.value
            if (memoList.isEmpty()) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        stringResource(R.string.no_memos),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(memoList) { memo ->
                        MemoItemRow(
                            memo = memo,
                            onMemoSelected = onMemoSelected,
                            isSelected = selectedMemoIds.value.contains(memo.id),
                            isSelectionMode = isSelectionMode.value,
                            onLongPress = { viewModel.toggleMemoSelection(memo.id) },
                            onToggleSelection = { viewModel.toggleMemoSelection(memo.id) }
                        )
                    }
                }
            }
        }
    }

    if (showDeleteConfirmDialog.value) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirmDialog.value = false },
            title = { Text("${selectedMemoIds.value.size}件のメモを削除しますか？") },
            text = { Text("この操作は取り消せません。") },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.deleteSelectedMemos()
                        showDeleteConfirmDialog.value = false
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Text("削除")
                }
            },
            dismissButton = {
                Button(onClick = { showDeleteConfirmDialog.value = false }) {
                    Text("キャンセル")
                }
            }
        )
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun MemoItemRow(
    memo: Memo,
    onMemoSelected: (Long) -> Unit,
    isSelected: Boolean,
    isSelectionMode: Boolean,
    onLongPress: () -> Unit,
    onToggleSelection: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                if (isSelected) MaterialTheme.colorScheme.primaryContainer else Color.Transparent
            )
            .combinedClickable(
                onClick = {
                    if (isSelectionMode) {
                        onToggleSelection()
                    } else {
                        onMemoSelected(memo.id)
                    }
                },
                onLongClick = onLongPress
            ),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                memo.title,
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                memo.body.take(100),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 2,
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                formatTimestamp(memo.createdAt),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun ListeningStatusBar(recognizedText: String) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
            .padding(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Row(
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            CircularProgressIndicator(modifier = Modifier.width(20.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                stringResource(R.string.recording),
                style = MaterialTheme.typography.labelLarge
            )
        }

        if (recognizedText.isNotBlank()) {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                recognizedText,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(8.dp)
            )
        }
    }
}

private fun formatTimestamp(millis: Long): String {
    val formatter = SimpleDateFormat("MMM dd, yyyy HH:mm", Locale.getDefault())
    return formatter.format(Date(millis))
}
