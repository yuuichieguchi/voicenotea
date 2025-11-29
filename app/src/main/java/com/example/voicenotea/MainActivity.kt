package com.example.voicenotea

import android.Manifest
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.voicenotea.ui.MemoDetailViewModel
import com.example.voicenotea.ui.MemoListViewModel
import com.example.voicenotea.ui.screens.MemoDetailScreen
import com.example.voicenotea.ui.screens.MemoListScreen
import com.example.voicenotea.ui.theme.VoicenotaTheme

class MainActivity : ComponentActivity() {
    private val requestPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
            if (!isGranted) {
                // Permission denied; user should not be able to record.
                // The UI will reflect this state.
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)

        setContent {
            VoicenotaTheme {
                VoicenotaApp(this)
            }
        }
    }
}

@Composable
fun VoicenotaApp(activity: MainActivity) {
    val navController = rememberNavController()
    val memoListViewModel = MemoListViewModel(activity)
    val memoDetailViewModel = MemoDetailViewModel(activity)

    NavHost(
        navController = navController,
        startDestination = "memo_list"
    ) {
        composable("memo_list") {
            MemoListScreen(
                viewModel = memoListViewModel,
                onMemoSelected = { memoId ->
                    navController.navigate("memo_detail/$memoId")
                }
            )
        }

        composable(
            route = "memo_detail/{memoId}",
            arguments = listOf(
                navArgument("memoId") { type = NavType.LongType }
            )
        ) { backStackEntry ->
            val memoId = backStackEntry.arguments?.getLong("memoId") ?: 0L
            MemoDetailScreen(
                viewModel = memoDetailViewModel,
                memoId = memoId,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
