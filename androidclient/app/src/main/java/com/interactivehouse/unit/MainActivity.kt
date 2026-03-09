package com.interactivehouse.unit

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import com.interactivehouse.unit.data.repo.SocketSmartHomeRepository
import com.interactivehouse.unit.ui.SmartHomeViewModel
import com.interactivehouse.unit.ui.navigation.AppRoot
import com.interactivehouse.unit.ui.theme.InteractiveHouseUnitTheme

class MainActivity : ComponentActivity() {

    private val vm by lazy { SmartHomeViewModel(SocketSmartHomeRepository()) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            InteractiveHouseUnitTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    containerColor = MaterialTheme.colorScheme.background
                ) { innerPadding ->
                    Box(modifier = Modifier.padding(innerPadding)) {
                        AppRoot(vm)
                    }
                }
            }
        }
    }
}