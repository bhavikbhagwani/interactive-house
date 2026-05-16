package com.interactivehouse.unit.ui.dynamic

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.interactivehouse.unit.R
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
    val friendlyTitle = friendlyDeviceName(title)
    val subtitle = deviceSubtitle(title)
    val statusText = readableState(title, latestState)
    val iconRes = deviceIconRes(title)

    Box(modifier = Modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(240.dp)
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

        Column(modifier = Modifier.fillMaxSize()) {
            Spacer(modifier = Modifier.height(28.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(horizontalAlignment = Alignment.Start) {
                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .clip(RoundedCornerShape(18.dp))
                            .background(Color.White.copy(alpha = 0.15f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Image(
                            painter = painterResource(id = iconRes),
                            contentDescription = friendlyTitle,
                            modifier = Modifier.size(32.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    Text(
                        text = friendlyTitle,
                        style = MaterialTheme.typography.headlineMedium,
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = subtitle,
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.92f)
                    )
                }

                TextButton(onClick = onBack) {
                    Text("Back", color = Color.White)
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
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.errorContainer
                            )
                        ) {
                            Text(
                                text = error,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                modifier = Modifier.padding(14.dp)
                            )
                        }

                        Spacer(modifier = Modifier.height(14.dp))
                    }

                    if (uiDefinition == null) {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator()
                        }
                        return@Surface
                    }

                    Card(
                        modifier = Modifier.fillMaxWidth(),
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
                            Box(
                                modifier = Modifier
                                    .size(54.dp)
                                    .clip(RoundedCornerShape(16.dp))
                                    .background(Color(0xFFDCE6FF)),
                                contentAlignment = Alignment.Center
                            ) {
                                Image(
                                    painter = painterResource(id = iconRes),
                                    contentDescription = friendlyTitle,
                                    modifier = Modifier.size(26.dp)
                                )
                            }

                            Column {
                                Text(
                                    text = "Current Status",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.SemiBold
                                )

                                Spacer(modifier = Modifier.height(4.dp))

                                Text(
                                    text = statusText,
                                    style = MaterialTheme.typography.headlineSmall,
                                    color = Color(0xFF1F2A5A),
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(22.dp))

                    Text(
                        text = if (uiDefinition.controls.isEmpty()) {
                            "Sensor Information"
                        } else {
                            "Available Actions"
                        },
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    if (uiDefinition.controls.isEmpty()) {
                        SensorStateDetails(latestState)
                    } else {
                        SmartControls(
                            deviceTitle = title,
                            controls = uiDefinition.controls,
                            latestState = latestState,
                            onAction = onAction
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun SensorStateDetails(latestState: Map<String, Any>) {
    if (latestState.isEmpty()) {
        Text(
            text = "No state information available.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        return
    }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        latestState.forEach { (key, value) ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = formatStateLabel(key),
                        fontWeight = FontWeight.SemiBold
                    )

                    Text(text = formatStateValue(value))
                }
            }
        }
    }
}

@Composable
private fun SmartControls(
    deviceTitle: String,
    controls: List<Control>,
    latestState: Map<String, Any>,
    onAction: (String) -> Unit
) {
    val visibleControls = filteredControls(deviceTitle, controls, latestState)

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        visibleControls.forEach { control ->
            val disabledFromRule = control.disabledWhen?.let { rule ->
                val value = latestState[rule.stateKey]
                (value is Boolean) && (value == rule.equals)
            } ?: false

            val disabledFromEnabled = control.enabled == false
            val disabled = disabledFromRule || disabledFromEnabled

            Button(
                onClick = { onAction(control.action) },
                enabled = !disabled,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(18.dp)
            ) {
                Text(
                    text = improvedActionLabel(deviceTitle, control.label, latestState),
                    style = MaterialTheme.typography.labelLarge
                )
            }
        }
    }
}

private fun filteredControls(
    deviceTitle: String,
    controls: List<Control>,
    latestState: Map<String, Any>
): List<Control> {
    return controls
}

private fun improvedActionLabel(
    deviceTitle: String,
    originalLabel: String,
    latestState: Map<String, Any>
): String {
    return originalLabel
}

private fun friendlyDeviceName(rawTitle: String): String {
    val t = rawTitle.trim().lowercase()

    return when {
        "led" in t || "light" in t -> {
            val number = t.substringAfterLast("-", "")
            if (number.isNotEmpty()) "Light $number" else "Light"
        }

        "fan" in t -> {
            val number = t.substringAfterLast("-", "")
            if (number.isNotEmpty()) "Fan $number" else "Fan"
        }

        "servo" in t || "window" in t -> "Window"
        "door" in t || "lock" in t -> "Door Lock"
        "coffee" in t -> "Coffee Machine"
        "motion" in t -> "Motion Sensor"
        "smoke" in t -> "Smoke Sensor"
        "temp" in t || "temperature" in t -> "Steam Sensor"
        "alarm" in t || "buzzer" in t -> "Alarm"

        else -> rawTitle
    }
}

private fun deviceSubtitle(rawTitle: String): String {
    val t = rawTitle.trim().lowercase()

    return when {
        "led" in t || "light" in t -> "Adjust your room lighting"
        "fan" in t -> "Control the fan"
        "servo" in t || "window" in t -> "Open or close the window"
        "door" in t || "lock" in t -> "Manage your home access"
        "coffee" in t -> "Start your coffee anytime"
        "motion" in t -> "Monitor room movement"
        "smoke" in t -> "Monitor smoke detection"
        "temp" in t || "temperature" in t -> "Monitor humidity"
        "alarm" in t || "buzzer" in t -> "Monitor or control alarm status"

        else -> "Control your connected device"
    }
}

private fun readableState(rawTitle: String, latestState: Map<String, Any>): String {
    val t = rawTitle.lowercase()

    return when {
        "led" in t || "light" in t -> when {
            latestState["ledOn"] == true || latestState["lightOn"] == true -> "On"
            latestState["ledOn"] == false || latestState["lightOn"] == false -> "Off"
            else -> "Unknown"
        }

        "fan" in t -> when {
            latestState["fanOn"] == true -> "On"
            latestState["fanOn"] == false -> "Off"
            else -> "Unknown"
        }

        "servo" in t || "window" in t -> when (val pos = latestState["position"]) {
            90, 90.0 -> "Open"
            0, 0.0 -> "Closed"
            else -> if (pos != null) pos.toString() else "Unknown"
        }

        "door" in t || "lock" in t -> when {
            latestState["locked"] == true -> "Locked"
            latestState["locked"] == false -> "Unlocked"

            latestState["doorState"] is String ->
                (latestState["doorState"] as String).replaceFirstChar { it.uppercase() }

            latestState["doorState"] == 0 || latestState["doorState"] == 0.0 -> "Close"
            latestState["doorState"] == 180 || latestState["doorState"] == 180.0 -> "Open"
            latestState["doorState"] == 90 || latestState["doorState"] == 90.0 -> "Stop"

            else -> "Unknown"
        }

        "coffee" in t -> when {
            latestState["isMaking"] == true -> "Brewing"
            latestState["isMaking"] == false -> "Ready"
            else -> "Unknown"
        }

        "motion" in t -> when {
            latestState["motionDetected"] == true -> "Motion Detected"
            latestState["motionDetected"] == false -> "No Motion"
            else -> "Unknown"
        }

        "smoke" in t -> when {
            latestState["smokeDetected"] == true -> "Smoke Detected"
            latestState["smokeDetected"] == false -> "Clear"
            else -> "Unknown"
        }

        "temp" in t || "temperature" in t -> {
            val level = latestState["steamLevel"] ?: latestState["temperature"]
            if (level != null) "Level: $level" else "Unknown"
        }

        "alarm" in t || "buzzer" in t -> when {
            latestState["alarmOn"] == true || latestState["buzzerOn"] == true -> "On"
            latestState["alarmOn"] == false || latestState["buzzerOn"] == false -> "Off"
            else -> "Unknown"
        }

        else -> "Unknown"
    }
}

private fun deviceIconRes(rawTitle: String): Int {
    val t = rawTitle.lowercase()

    return when {
        "led" in t || "light" in t -> R.drawable.lightbulb
        "door" in t || "lock" in t -> R.drawable.door
        "coffee" in t -> R.drawable.coffee_cup

        // Safe fallback icons because fan/window drawables caused build errors
        "fan" in t -> R.drawable.fan
        "servo" in t || "window" in t -> R.drawable.window
        "motion" in t -> R.drawable.motion_sensor
        "smoke" in t -> R.drawable.vape
        "temp" in t || "temperature" in t -> R.drawable.thermometer
        "alarm" in t || "buzzer" in t -> R.drawable.siren

        else -> R.drawable.lightbulb
    }
}

private fun formatStateLabel(key: String): String {
    return when (key) {
        "smokeLevel" -> "Smoke Level"
        "smokeDetected" -> "Smoke Detected"
        "threshold" -> "Threshold"
        "steamLevel" -> "Steam Level"
        "status" -> "Status"
        "thresholdHigh" -> "High Threshold"
        "thresholdLow" -> "Low Threshold"
        "temperature" -> "Steam Level"
        "alarmOn" -> "Alarm On"
        "fanOn" -> "Fan On"
        "ledOn" -> "Light On"
        "doorState" -> "Door State"
        "position" -> "Position"
        else -> key
    }
}

private fun formatStateValue(value: Any): String {
    return when (value) {
        true -> "Yes"
        false -> "No"
        else -> value.toString()
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
private fun LightDeviceScreenPreview() {
    MaterialTheme {
        DeviceScreen(
            title = "light-1",
            uiDefinition = null,
            latestState = mapOf("lightOn" to false),
            error = null,
            onBack = {},
            onAction = {}
        )
    }
}