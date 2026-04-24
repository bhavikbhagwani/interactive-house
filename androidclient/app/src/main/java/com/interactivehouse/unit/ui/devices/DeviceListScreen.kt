package com.interactivehouse.unit.ui.devices

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.interactivehouse.unit.data.models.Device
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.foundation.Image
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.graphics.ColorFilter
import com.interactivehouse.unit.R

@Composable
fun DeviceListScreen(
    devices: List<Device>,
    deviceStates: Map<String, Map<String, Any>>,
    isLoading: Boolean,
    error: String?,
    onRefresh: () -> Unit,
    onSelect: (Device) -> Unit
) {
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(220.dp)
                .background(
                    brush = Brush.verticalGradient(
                        colors = listOf(
                            Color(0xFF6F86B6),
                            Color(0xFF2C3E73),
                            Color(0xFF0D1333)
                        )
                    )
                )
        )

        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            Spacer(modifier = Modifier.height(34.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column {
                    Text(
                        text = "Devices",
                        style = MaterialTheme.typography.headlineMedium,
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "What would you like to control today?",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.9f)
                    )
                }

                TextButton(
                    onClick = onRefresh,
                    enabled = !isLoading
                ) {
                    Text(
                        text = if (isLoading) "Loading..." else "Refresh",
                        color = Color.White
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Surface(
                modifier = Modifier.fillMaxSize(),
                color = MaterialTheme.colorScheme.background,
                shape = RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp),
                tonalElevation = 2.dp,
                shadowElevation = 4.dp
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 18.dp, vertical = 20.dp)
                ) {
                    if (!error.isNullOrBlank()) {
                        Card(
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.errorContainer
                            ),
                            shape = RoundedCornerShape(16.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = error,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                modifier = Modifier.padding(14.dp)
                            )
                        }

                        Spacer(modifier = Modifier.height(12.dp))
                    }

                    if (isLoading && devices.isEmpty()) {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator()
                        }
                    } else if (!isLoading && devices.isEmpty()) {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "No devices available",
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else {
                        LazyColumn(
                            verticalArrangement = Arrangement.spacedBy(14.dp),
                            contentPadding = PaddingValues(bottom = 20.dp)
                        ) {
                            items(devices) { device ->
                                val state = deviceStates[device.deviceId]
                                val statusText = readableStatus(device.deviceType, state)

                                Card(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { onSelect(device) },
                                    shape = RoundedCornerShape(22.dp),
                                    elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
                                ) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(18.dp),
                                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        DeviceIcon(device.deviceType)

                                        Column(
                                            modifier = Modifier.weight(1f),
                                            verticalArrangement = Arrangement.spacedBy(6.dp)
                                        ) {
                                            Text(
                                                text = friendlyName(device.deviceType, device.deviceId),
                                                style = MaterialTheme.typography.titleLarge,
                                                fontWeight = FontWeight.SemiBold,
                                                maxLines = 1
                                            )

                                            Text(
                                                text = "Tap to view controls",
                                                style = MaterialTheme.typography.bodyMedium,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                                maxLines = 1
                                            )

                                            StatusChip(statusText)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusChip(text: String) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(50))
            .background(Color(0xFFDCE6FF))
            .padding(horizontal = 10.dp, vertical = 5.dp)
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelMedium,
            color = Color(0xFF1F2A5A),
            fontWeight = FontWeight.SemiBold,
            maxLines = 1
        )
    }
}

@Composable
private fun DeviceIcon(deviceType: String) {
    val iconRes = when {
        deviceType.contains("led", ignoreCase = true) ||
                deviceType.contains("light", ignoreCase = true) -> R.drawable.lightbulb

        deviceType.contains("door", ignoreCase = true) ||
                deviceType.contains("lock", ignoreCase = true) -> R.drawable.door

        deviceType.contains("fan", ignoreCase = true) -> R.drawable.fan

        deviceType.contains("servo", ignoreCase = true) ||
                deviceType.contains("window", ignoreCase = true) -> R.drawable.window

        deviceType.contains("coffee", ignoreCase = true) -> R.drawable.coffee_cup

        else -> R.drawable.lightbulb
    }

    Image(
        painter = painterResource(id = iconRes),
        contentDescription = deviceType,
        modifier = Modifier.size(28.dp)
    )
}



private fun readableStatus(
    deviceType: String,
    state: Map<String, Any>?
): String {
    if (state == null || state.isEmpty()) return "Unknown"

    val type = deviceType.trim().lowercase()

    return when {
        "led" in type || "light" in type -> when {
            state["ledOn"] == true || state["lightOn"] == true -> "ON"
            state["ledOn"] == false || state["lightOn"] == false -> "OFF"
            else -> "Unknown"
        }

        "fan" in type -> when {
            state["fanOn"] == true -> "ON"
            state["fanOn"] == false -> "OFF"
            else -> "Unknown"
        }

        "servo" in type || "window" in type -> when (val pos = state["position"]) {
            90, 90.0 -> "OPEN"
            0, 0.0 -> "CLOSED"
            else -> if (pos != null) pos.toString() else "Unknown"
        }

        "door" in type || "lock" in type -> when {
            state["locked"] == true -> "LOCKED"
            state["locked"] == false -> "UNLOCKED"

            state["doorState"] is String -> (state["doorState"] as String).uppercase()
            state["doorState"] == 0 || state["doorState"] == 0.0 -> "CLOSE"
            state["doorState"] == 180 || state["doorState"] == 180.0 -> "OPEN"
            state["doorState"] == 90 || state["doorState"] == 90.0 -> "STOP"

            else -> "Unknown"
        }

        "coffee" in type -> when {
            state["isMaking"] == true -> "MAKING COFFEE"
            state["isMaking"] == false -> "IDLE"
            else -> "Unknown"
        }

        else -> "Unknown"
    }
}

private fun friendlyName(deviceType: String, deviceId: String): String {
    val type = deviceType.trim().lowercase()
    val id = deviceId.lowercase()

    return when {
        "led" in type || "light" in type -> {
            val number = id.substringAfterLast("-", "")
            if (number.isNotEmpty()) "Light $number" else "Light"
        }

        "fan" in type -> {
            val number = id.substringAfterLast("-", "")
            if (number.isNotEmpty()) "Fan $number" else "Fan"
        }

        "servo" in type || "window" in type -> "Window"
        "door" in type || "lock" in type -> "Door Lock"
        "coffee" in type -> "Coffee Machine"

        else -> deviceType
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
private fun DeviceListScreenPreview() {
    MaterialTheme {
        DeviceListScreen(
            devices = listOf(
                Device(deviceId = "coffee-machine-1", deviceType = "coffee_machine"),
                Device(deviceId = "door-1", deviceType = "door"),
                Device(deviceId = "light-1", deviceType = "light")
            ),
            deviceStates = mapOf(
                "coffee-machine-1" to mapOf("isMaking" to false),
                "door-1" to mapOf("locked" to true),
                "light-1" to mapOf("lightOn" to false)
            ),
            isLoading = false,
            error = null,
            onRefresh = {},
            onSelect = {}
        )
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
private fun DeviceListScreenEmptyPreview() {
    MaterialTheme {
        DeviceListScreen(
            devices = emptyList(),
            deviceStates = emptyMap(),
            isLoading = false,
            error = null,
            onRefresh = {},
            onSelect = {}
        )
    }
}