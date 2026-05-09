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
                Box(
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
                    }

                    when {
                        isLoading && devices.isEmpty() -> {
                            Box(
                                modifier = Modifier.fillMaxSize(),
                                contentAlignment = Alignment.Center
                            ) {
                                CircularProgressIndicator()
                            }
                        }

                        !isLoading && devices.isEmpty() -> {
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
                        }

                        else -> {
                            LazyColumn(
                                modifier = Modifier.fillMaxSize(),
                                verticalArrangement = Arrangement.spacedBy(14.dp),
                                contentPadding = PaddingValues(
                                    top = if (!error.isNullOrBlank()) 80.dp else 0.dp,
                                    bottom = 32.dp
                                )
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
    val type = deviceType.trim().lowercase()

    val iconRes = when {
        "led" in type || "light" in type -> R.drawable.lightbulb
        "door" in type -> R.drawable.door
        "fan" in type -> R.drawable.fan
        "servo" in type || "window" in type -> R.drawable.window

        // If you do not have these drawable icons yet, keep lightbulb as fallback
        "motion" in type -> R.drawable.lightbulb
        "smoke" in type -> R.drawable.lightbulb
        "temp" in type || "temperature" in type -> R.drawable.lightbulb
        "alarm" in type || "buzzer" in type -> R.drawable.lightbulb

        else -> R.drawable.lightbulb
    }

    Box(
        modifier = Modifier
            .size(52.dp)
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0xFFDCE6FF)),
        contentAlignment = Alignment.Center
    ) {
        Image(
            painter = painterResource(id = iconRes),
            contentDescription = null,
            modifier = Modifier.size(26.dp),
            colorFilter = ColorFilter.tint(Color(0xFF1F2A5A))
        )
    }
}



private fun readableStatus(
    deviceType: String,
    state: Map<String, Any>?
): String {
    if (state == null || state.isEmpty()) return "Unknown"

    val type = deviceType.trim().lowercase()

    return when {
        "led" in type || "light" in type -> when (state["ledOn"] ?: state["lightOn"]) {
            true -> "ON"
            false -> "OFF"
            else -> "Unknown"
        }

        "fan" in type -> when (state["fanOn"]) {
            true -> "ON"
            false -> "OFF"
            else -> "Unknown"
        }

        "servo" in type || "window" in type -> when (val pos = state["position"]) {
            90, 90.0 -> "OPEN"
            0, 0.0 -> "CLOSED"
            else -> if (pos != null) pos.toString() else "Unknown"
        }

        "door" in type -> when (val doorState = state["doorState"] ?: state["locked"]) {
            is String -> doorState.uppercase()
            true -> "LOCKED"
            false -> "UNLOCKED"
            0, 0.0 -> "CLOSE"
            180, 180.0 -> "OPEN"
            90, 90.0 -> "STOP"
            else -> "Unknown"
        }

        "motion" in type -> when (state["motionDetected"]) {
            true -> "MOTION"
            false -> "NO MOTION"
            else -> "Unknown"
        }

        "smoke" in type -> when (state["smokeDetected"]) {
            true -> "SMOKE"
            false -> "CLEAR"
            else -> "Unknown"
        }

        "temp" in type || "temperature" in type -> {
            val temp = state["temperature"]
            if (temp != null) "$temp°C" else "Unknown"
        }

        "alarm" in type || "buzzer" in type -> when (state["alarmOn"] ?: state["buzzerOn"]) {
            true -> "ON"
            false -> "OFF"
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
            "LED Light ${number.ifEmpty { "" }}"
        }

        "fan" in type -> {
            val number = id.substringAfterLast("-", "")
            "Fan ${number.ifEmpty { "" }}"
        }

        "servo" in type || "window" in type -> "Window"

        "door" in type -> "Door"

        "motion" in type -> "Motion Sensor"

        "smoke" in type -> "Smoke Sensor"

        "temp" in type || "temperature" in type -> "Temperature Sensor"

        "alarm" in type || "buzzer" in type -> "Alarm"

        else -> deviceType
    }
}

