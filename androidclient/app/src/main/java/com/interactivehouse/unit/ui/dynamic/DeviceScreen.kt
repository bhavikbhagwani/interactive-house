package com.interactivehouse.unit.ui.dynamic

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.interactivehouse.unit.data.models.Control
import com.interactivehouse.unit.data.models.UiDefinition

@Composable
fun DeviceScreen(
    title: String,
    uiDefinition: UiDefinition?,
    latestState: Map<String, Any>,
    error: String?,
    onBack: () -> Unit,
    onAction: (String) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(title, style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = onBack) { Text("Back") }
        }

        if (!error.isNullOrBlank()) {
            Spacer(Modifier.height(8.dp))
            Text(error, color = MaterialTheme.colorScheme.error)
        }

        Spacer(Modifier.height(14.dp))

        if (uiDefinition == null) {
            CircularProgressIndicator()
            return
        }

        // Optional state display (useful for demo)
        if (latestState.isNotEmpty()) {
            Text("State: $latestState", style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(12.dp))
        }

        DynamicControls(
            controls = uiDefinition.controls,
            latestState = latestState,
            onAction = onAction
        )
    }
}

@Composable
private fun DynamicControls(
    controls: List<Control>,
    latestState: Map<String, Any>,
    onAction: (String) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        controls.forEach { c ->
            when (c.kind) {
                "button" -> {
                    val disabled = c.disabledWhen?.let { rule ->
                        val v = latestState[rule.stateKey]
                        (v is Boolean) && (v == rule.equals)
                    } ?: false

                    Button(
                        onClick = { onAction(c.action) },
                        enabled = !disabled,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(c.label)
                    }
                }
                else -> {
                    Text("Unknown control type: ${c.kind}")
                }
            }
        }
    }
}