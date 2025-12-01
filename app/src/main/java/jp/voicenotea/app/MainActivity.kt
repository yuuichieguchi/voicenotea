package jp.voicenotea.app

import android.Manifest
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import jp.voicenotea.app.ui.MemoDetailViewModel
import jp.voicenotea.app.ui.MemoListViewModel
import jp.voicenotea.app.ui.MemoDetailViewModelFactory
import jp.voicenotea.app.ui.MemoListViewModelFactory
import jp.voicenotea.app.ui.screens.MemoDetailScreen
import jp.voicenotea.app.ui.screens.MemoListScreen
import jp.voicenotea.app.ui.theme.VoicenotaTheme

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
    val listFactory = MemoListViewModelFactory(activity)
    val memoListViewModel = ViewModelProvider(activity, listFactory).get(MemoListViewModel::class.java)

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
            val factory = MemoDetailViewModelFactory(activity)
            val memoDetailViewModel = ViewModelProvider(activity, factory).get(MemoDetailViewModel::class.java)

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
