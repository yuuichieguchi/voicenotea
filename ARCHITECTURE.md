# Voicenotea Architecture Guide

## Overview

Voicenotea implements a clean, production-ready Android architecture using **MVVM + Repository Pattern**. This document explains the design decisions and how each layer works.

## Architecture Layers

### 1. UI Layer (Presentation)

**Location**: `ui/screens/` and `MainActivity.kt`

The UI layer is built with **Jetpack Compose** and uses a single-activity architecture with Navigation Compose.

**Components**:
- `MainActivity`: Single entry point, handles permissions, sets up Navigation host
- `MemoListScreen`: Composable showing memo list with recording controls (FAB)
- `MemoDetailScreen`: Composable for viewing and editing individual memos
- `Theme.kt`: Material 3 theming configuration

**Key Points**:
- No business logic in Composables—only UI rendering and event delegation
- State flows from ViewModels via `collectAsState()`
- Navigation between screens using sealed routes

### 2. ViewModel Layer (State & Orchestration)

**Location**: `ui/MemoListViewModel.kt`, `ui/MemoDetailViewModel.kt`

ViewModels manage UI state and coordinate interactions between the UI and lower layers.

**MemoListViewModel**:
- Manages recording state (Idle → Recording → Transcribing → Idle)
- Holds memos Flow from repository
- Orchestrates audio recording → transcription → memo persistence
- Tracks error messages and displays them via Snackbars

**MemoDetailViewModel**:
- Loads a single memo by ID
- Manages editable title and body fields
- Saves changes to the repository
- Handles memo deletion

**Recording State Machine**:
```kotlin
sealed class RecordingState {
    object Idle : RecordingState()
    data class Recording(val durationMs: Long = 0) : RecordingState()
    object Transcribing : RecordingState()
}
```

### 3. Repository Layer (Data Abstraction)

**Location**: `data/MemoRepository.kt`

The repository pattern provides a single source of truth for data access. It abstracts the underlying data source (Room database).

**Interface**:
```kotlin
interface MemoRepository {
    fun getAllMemos(): Flow<List<Memo>>
    suspend fun getMemoById(id: Long): Memo?
    suspend fun insertMemo(memo: Memo): Long
    suspend fun updateMemo(memo: Memo)
    suspend fun deleteMemoById(id: Long)
}
```

**Implementation**:
- `MemoRepositoryImpl`: Wraps `MemoDao` and delegates all calls
- Enables easy mocking in tests
- Can be extended to support multiple data sources (cloud sync, etc.)

### 4. Domain Layer (Business Logic)

**Location**: `domain/`

Contains core business logic not tied to any framework.

**AudioRecorder**:
- Wraps MediaRecorder API
- Handles lifecycle (start, stop, cancel)
- Saves .m4a files to app-private cache
- Properly cleans up resources on error

**TranscriptionService**:
- Interface for transcription logic
- `FakeTranscriptionService`: Stub implementation returning dummy text
- **Integration point**: Replace fake implementation with real API call (Azure Speech, Google Cloud, FastAPI backend)

### 5. Data Layer (Persistence)

**Location**: `data/`

Uses Room ORM for SQLite database management.

**Components**:

**Memo Entity**:
```kotlin
@Entity(tableName = "memos")
data class Memo(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val title: String,
    val body: String,
    val audioFilePath: String,
    val createdAt: Long = Instant.now().toEpochMilli(),
    val updatedAt: Long = Instant.now().toEpochMilli()
)
```

**MemoDao**:
- Query methods: `getAllMemos()`, `getMemoById()`
- Mutation methods: `insertMemo()`, `updateMemo()`, `deleteMemo()`
- Returns Flows for reactive updates

**MemoDatabase**:
- Singleton pattern with thread-safe double-checked locking
- Single-database design (one table: `memos`)
- Version 1

## Data Flow

### Recording and Transcription Flow

```
User taps FAB (Start Recording)
    ↓
AudioRecorder.startRecording()
    ↓
MediaRecorder captures audio → File saved (.m4a)
    ↓
User taps FAB (Stop Recording)
    ↓
AudioRecorder.stopRecording() → returns audio File
    ↓
State → Transcribing (UI shows progress)
    ↓
TranscriptionService.transcribeAudio(file)
    ↓
Fake service returns: "This is a fake transcript..."
    ↓
Create Memo object with:
  - title = first 50 chars of transcript
  - body = full transcript
  - audioFilePath = saved audio file path
  - createdAt = now
    ↓
Repository.insertMemo(memo)
    ↓
Room DAO inserts into database
    ↓
MemoListScreen observes memos Flow → UI updates with new memo
    ↓
State → Idle
```

### Detail Screen Edit and Save Flow

```
User taps memo in list
    ↓
NavController navigates with memoId argument
    ↓
MemoDetailScreen launched
    ↓
MemoDetailViewModel.loadMemo(memoId)
    ↓
Repository.getMemoById(memoId)
    ↓
DAO query returns Memo
    ↓
State updated: memo, title, body StateFlows
    ↓
UI renders editable TextFields with current values
    ↓
User edits title/body and taps Save
    ↓
MemoDetailViewModel.saveMemo()
    ↓
Create updated Memo with new title, body, updatedAt timestamp
    ↓
Repository.updateMemo(updatedMemo)
    ↓
DAO executes UPDATE query
    ↓
Success → State updated, UI reflects changes
    ↓
User can tap back to return to list
```

## Coroutine Management

All async operations use **Kotlin coroutines** with proper scope management:

- **viewModelScope**: All ViewModel operations (DB queries, API calls)
- **Main dispatcher**: Used implicitly for UI updates via StateFlow
- **Default dispatcher**: Could be used for heavy computations (not needed here)

Example:
```kotlin
fun saveMemo() {
    viewModelScope.launch {  // Launches on Main dispatcher
        try {
            repository.updateMemo(updatedMemo)  // suspend function
            _memo.value = updatedMemo
        } catch (e: Exception) {
            _errorMessage.value = "Failed: ${e.message}"
        }
    }
}
```

## Permission Handling

Runtime permission for `RECORD_AUDIO` is requested via `ActivityResultContracts.RequestPermission()`:

```kotlin
private val requestPermissionLauncher =
    registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
        // isGranted = true if user granted, false if denied
    }

override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
    // ...
}
```

The UI gracefully handles permission denial by preventing recording operations.

## Error Handling Strategy

1. **Recording Errors**: Caught in `AudioRecorder.startRecording()` → returns null → ViewModel detects and shows snackbar
2. **Transcription Errors**: Caught in `transcribeAndSaveMemo()` → `_errorMessage` StateFlow → UI displays snackbar
3. **Database Errors**: Try-catch in ViewModel launch block → `_errorMessage` updated
4. **Lifecycle Errors**: MediaRecorder resource cleanup in `AudioRecorder.cleanup()`

Snackbar display:
```kotlin
LaunchedEffect(errorMessage.value) {
    errorMessage.value?.let { message ->
        snackbarHostState.showSnackbar(message)
        viewModel.clearError()
    }
}
```

## Testing Strategy

### Unit Testing

**Repository & DAO**: Mock with in-memory Room database
```kotlin
@get:Rule
val instantExecutorRule = InstantTaskExecutorRule()

private lateinit var database: MemoDatabase
private lateinit var dao: MemoDao

@Before
fun setup() {
    database = Room.inMemoryDatabaseBuilder(
        ApplicationProvider.getApplicationContext(),
        MemoDatabase::class.java
    ).build()
    dao = database.memoDao()
}

@Test
fun insertMemoAndRetrieve() = runTest {
    val memo = Memo(title = "Test", body = "Content", audioFilePath = "/path")
    dao.insertMemo(memo)
    val loaded = dao.getMemoById(1)
    assertEquals("Test", loaded?.title)
}
```

**ViewModel**: Mock repository
```kotlin
@Test
fun recordingFlow() = runTest {
    val mockRepo = mockk<MemoRepository>()
    val viewModel = MemoListViewModel(mockRepo)

    viewModel.startRecording()
    assertEquals(RecordingState.Recording::class, viewModel.recordingState.value::class)
}
```

### UI Testing

**Compose Previews**:
```kotlin
@Preview(showBackground = true)
@Composable
fun MemoListScreenPreview() {
    MemoListScreen(
        viewModel = MemoListViewModel(context),
        onMemoSelected = {}
    )
}
```

## Integration with Real Transcription Services

### Option 1: Azure Speech to Text

```kotlin
class AzureSpeechTranscriptionService(
    private val apiKey: String,
    private val region: String
) : TranscriptionService {
    override suspend fun transcribeAudio(file: File): String {
        val client = createHttpClient(apiKey, region)
        val formData = file.readBytes()
        val response = client.post(
            "https://$region.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        ) {
            setBody(formData)
        }
        return response.text
    }
}
```

### Option 2: Custom FastAPI Backend

```kotlin
class FastAPITranscriptionService(private val apiClient: HttpClient) : TranscriptionService {
    override suspend fun transcribeAudio(file: File): String {
        val formData = file.readBytes()
        val response = apiClient.submitForm(
            url = "http://your-api.com/transcribe",
            formParameters = parameters {
                append("audio", formData)
            }
        )
        return response.jsonObject["text"]?.jsonPrimitive?.content ?: ""
    }
}
```

### Switching Implementation

In `MainActivity`:
```kotlin
private val transcriptionService: TranscriptionService =
    when {
        BuildConfig.DEBUG -> FakeTranscriptionService()
        else -> AzureSpeechTranscriptionService(apiKey, region)
    }
```

## Dependency Injection (Future Enhancement)

Currently, ViewModels create their own instances. For scalability, consider **Hilt**:

```kotlin
@HiltViewModel
class MemoListViewModel @Inject constructor(
    private val repository: MemoRepository,
    private val audioRecorder: AudioRecorder,
    private val transcriptionService: TranscriptionService
) : ViewModel() { ... }
```

## Performance Considerations

1. **Memory**: Audio files stored in cache; periodically clean up old files
2. **Database**: Indexed by `createdAt` DESC for fast list queries
3. **Coroutines**: All DB operations on IO dispatcher implicitly via Room
4. **Compose**: LazyColumn for memo list (only renders visible items)

## Security Considerations

1. **Permissions**: Request `RECORD_AUDIO` at runtime, handle denial gracefully
2. **File Storage**: Audio in app-private cache (not world-readable)
3. **Database**: No encryption (can add Room's encrypted database if needed)
4. **API Keys**: Use BuildConfig or environment variables, never hardcode

## Summary

Voicenotea demonstrates professional Android architecture with:
✅ Clear separation of concerns (UI, ViewModel, Repository, Domain, Data)
✅ Reactive state management with StateFlow and Compose
✅ Coroutine best practices with proper scope management
✅ Type-safe Room database integration
✅ Ready for real transcription service integration
✅ Comprehensive error handling
✅ Testable design with dependency abstraction
