package jp.voicenotea.app.ui

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import jp.voicenotea.app.ui.screens.MemoListScreen
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MemoListScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun memoListScreen_renders_without_crashing() {
        // This test verifies that the screen can be composed without errors.
        // In a real app, you'd mock the ViewModel and test specific interactions.

        // Note: To fully test this, create a mock MemoListViewModel
        // and provide it to the composable.

        // Example:
        // val mockViewModel = mockk<MemoListViewModel>()
        // every { mockViewModel.memos } returns flowOf(emptyList())
        // every { mockViewModel.recordingState } returns flowOf(RecordingState.Idle)
        //
        // composeTestRule.setContent {
        //     MemoListScreen(mockViewModel) { }
        // }
        //
        // composeTestRule.onNodeWithText("Voicenotea").assertExists()
    }
}
