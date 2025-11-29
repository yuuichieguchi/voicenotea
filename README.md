# Voicenotea - Voice-to-Text Memo Pad

A minimal but production-quality Android app that converts speech to text in real-time and saves it as memos, using Android's native speech recognition.

## Architecture Overview

Voicenotea follows **MVVM + Repository pattern** with clean separation of concerns:

1. **UI Layer (Jetpack Compose)**: Declarative UI with single-activity architecture using Navigation Compose
2. **ViewModel Layer**: State management and speech recognition coordination
3. **Repository Layer**: Abstraction over data sources (Room database)
4. **Domain Layer**: Core business logic (SpeechRecognizerManager for native Android speech-to-text)
5. **Data Layer**: Room database with Entity, DAO, and Database setup

The app uses **Kotlin coroutines** for all async operations and **Android's native SpeechRecognizer API** for real-time speech-to-text conversion. No external transcription services are required—everything runs locally on the device.

## Project Structure

```
voicenotea/
├── app/
│   ├── src/main/
│   │   ├── AndroidManifest.xml
│   │   ├── java/com/example/voicenotea/
│   │   │   ├── MainActivity.kt
│   │   │   ├── data/
│   │   │   │   ├── Memo.kt                 (Room entity)
│   │   │   │   ├── MemoDao.kt              (Database access)
│   │   │   │   ├── MemoDatabase.kt         (Room database setup)
│   │   │   │   └── MemoRepository.kt       (Repository pattern)
│   │   │   ├── domain/
│   │   │   │   └── SpeechRecognizerManager.kt (Native speech-to-text)
│   │   │   ├── ui/
│   │   │   │   ├── MemoListViewModel.kt    (List screen state)
│   │   │   │   ├── MemoDetailViewModel.kt  (Detail screen state)
│   │   │   │   ├── screens/
│   │   │   │   │   ├── MemoListScreen.kt   (Composable list UI)
│   │   │   │   │   └── MemoDetailScreen.kt (Composable detail UI)
│   │   │   │   └── theme/
│   │   │   │       └── Theme.kt            (Material 3 theming)
│   │   └── res/
│   │       ├── values/
│   │       │   ├── strings.xml             (UI string resources)
│   │       │   └── themes.xml              (Theme definitions)
│   │       └── mipmap-anydpi-v33/          (App icon)
│   └── build.gradle.kts
├── build.gradle.kts
└── settings.gradle.kts
```

## Key Features

### 1. Real-Time Speech Recognition
- Uses Android's native **SpeechRecognizer API** (completely free, no external services)
- Converts spoken words to text in real-time
- Automatic silence detection (5 seconds of silence ends recognition)
- Shows recognized text while user is speaking

### 2. Automatic Memo Creation
- Text is automatically saved as a memo after speech recognition completes
- Auto-generated title from first 50 characters of transcript
- Full transcript stored as memo body
- No audio files stored (text only)

### 3. Data Storage
- Room database with Memo entity
- Fields: id, title, body, createdAt, updatedAt
- All database operations are coroutine-based (suspend functions)

### 4. UI Navigation
- Single-activity architecture with Jetpack Navigation Compose
- Two main screens:
  - **MemoListScreen**: Shows all memos with speech recording controls
  - **MemoDetailScreen**: Full-text editing and deletion
- Floating action button toggles between Start Listening / Stop Listening

### 5. State Management
- ViewModels use StateFlow for reactive state
- Sealed class `RecordingState` for clear state (Idle, Listening)
- Real-time text display while listening
- Coroutine scopes properly managed with viewModelScope

### 6. Error Handling
- Snackbars display errors (permission denied, network issues, no speech detected, etc.)
- Graceful fallbacks and resource cleanup
- Try-catch blocks in critical paths

## Getting Started

### Prerequisites
- Android Studio Hedgehog or later
- Kotlin 1.9.22+
- Minimum SDK 24 (Android 7.0)
- Target SDK 34

### Build and Run
```bash
cd voicenotea
./gradlew build
# Open in Android Studio and run on emulator/device
```

### Required Permissions
The app requests:
- `RECORD_AUDIO`: Access microphone for speech recognition

Permissions are requested at runtime via `ActivityResultContracts.RequestPermission()`.

## How It Works

### Speech-to-Text Flow
```
1. User taps "Start Listening" button (FAB)
2. SpeechRecognizer starts listening to microphone
3. User speaks
4. Recognized text displays in real-time on screen
5. After 5 seconds of silence, recognition automatically stops
6. Text is automatically saved as a new memo
7. Memo appears in the list
```

## Dependencies

Core libraries used:
- **Jetpack Compose**: Modern declarative UI framework
- **Room**: Local database persistence
- **Navigation Compose**: Single-activity navigation
- **Coroutines**: Async operations
- **ViewModel**: State management
- **Material 3**: UI components and theming

## Code Quality

- **MVVM + Repository Pattern**: Clean architecture with clear separation
- **Type Safety**: Full Kotlin type annotations, no `Any` usage
- **Coroutine Best Practices**: All async work in viewModelScope
- **Resource Management**: Proper lifecycle handling for SpeechRecognizer
- **Testing Ready**: Repository and service interfaces enable easy mocking
- **Privacy-First**: No external APIs, all processing on-device

## Future Enhancements

1. **Audio Playback**: Record and playback audio files alongside transcriptions
2. **Search**: Full-text search across memo bodies
3. **Cloud Sync**: Cloud backup of memos
4. **Export**: Save memos as PDF or text files
5. **Tags/Categories**: Organize memos by tags
6. **Multi-language**: Support for multiple languages in speech recognition
7. **Voice Commands**: Control app via voice commands

## License

MIT License - Feel free to use and modify as needed.
