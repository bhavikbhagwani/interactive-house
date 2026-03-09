package com.interactivehouse.unit.ui.devices

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.interactivehouse.unit.data.models.Device

@Composable
fun DeviceListScreen(
    devices: List<Device>,
    deviceStates: Map<String, Map<String, Any>>,
    isLoading: Boolean,
    error: String?,
    onRefresh: () -> Unit,
    onSelect: (Device) -> Unit
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
            Text("Devices", style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = onRefresh, enabled = !isLoading) { Text("Refresh") }
        }

        if (!error.isNullOrBlank()) {
            Spacer(Modifier.height(8.dp))
            Text(error, color = MaterialTheme.colorScheme.error)
        }

        Spacer(Modifier.height(12.dp))

        if (isLoading && devices.isEmpty()) {
            CircularProgressIndicator()
            return
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(devices) { d ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onSelect(d) }
                ) {
                    Column(Modifier.padding(14.dp)) {
                        Text(
                            friendlyName(d.deviceType),
                            style = MaterialTheme.typography.titleMedium
                        )
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "ID: ${d.deviceId}",
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }
            }
        }
    }
}

private fun friendlyName(deviceType: String): String {
    val t = deviceType
        .trim()
        .lowercase()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")

    return when (t) {
        "light" -> "Light"
        "door", "doorlock", "lock" -> "Door Lock"
        "coffeemachine", "coffee" -> "Coffee Machine"
        else -> deviceType
    }
}