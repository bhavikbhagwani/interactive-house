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

    Box(
        modifier = Modifier.fillMaxSize()
    ) {
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

        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            Spacer(modifier = Modifier.height(28.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(
                    horizontalAlignment = Alignment.Start
                ) {
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
                        text = "Available Actions",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )

                    Spacer(modifier = Modifier.height(12.dp))

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

@Composable
private fun SmartControls(
    deviceTitle: String,
    controls: List<Control>,
    latestState: Map<String, Any>,
    onAction: (String) -> Unit
) {
    val visibleControls = filteredControls(deviceTitle, controls, latestState)

    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        visibleControls.forEach { control ->
            val disabledFromRule = control.disabledWhen?.let { rule ->
                val value = latestState[rule.stateKey]
                (value is Boolean) && (value == rule.equals)
            } ?: false

            val disabledFromEnabled = control.enabled == false

            val disabledForCoffee =
                deviceTitle.contains("coffee", ignoreCase = true) &&
                        latestState["isMaking"] == true

            val disabled = disabledFromRule || disabledFromEnabled || disabledForCoffee

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
    val t = deviceTitle.lowercase()

    return when {
        "light" in t -> {
            val isOn = latestState["lightOn"] as? Boolean
            when (isOn) {
                true -> controls.filter {
                    it.label.equals("Turn OFF", ignoreCase = true) ||
                            it.action.equals("turn_off", ignoreCase = true)
                }
                false -> controls.filter {
                    it.label.equals("Turn ON", ignoreCase = true) ||
                            it.action.equals("turn_on", ignoreCase = true)
                }
                else -> controls
            }
        }

        "door" in t || "lock" in t -> {
            val locked = latestState["locked"] as? Boolean
            when (locked) {
                true -> controls.filter {
                    it.label.equals("Unlock", ignoreCase = true) ||
                            it.action.equals("unlock", ignoreCase = true)
                }
                false -> controls.filter {
                    it.label.equals("Lock", ignoreCase = true) ||
                            it.action.equals("lock", ignoreCase = true)
                }
                else -> controls
            }
        }

        "coffee" in t -> {
            controls
        }

        else -> controls
    }
}

private fun improvedActionLabel(
    deviceTitle: String,
    originalLabel: String,
    latestState: Map<String, Any>
): String {
    val t = deviceTitle.lowercase()

    return when {
        "coffee" in t && latestState["isMaking"] == true -> "Brewing..."
        "coffee" in t -> "Make Coffee"
        else -> originalLabel
    }
}

private fun friendlyDeviceName(rawTitle: String): String {
    val t = rawTitle.trim().lowercase()

    return when {
        "coffee" in t -> "Coffee Machine"
        "door" in t || "lock" in t -> "Door Lock"
        "light" in t -> "Light"
        else -> rawTitle
    }
}

private fun deviceSubtitle(rawTitle: String): String {
    val t = rawTitle.trim().lowercase()

    return when {
        "coffee" in t -> "Start your coffee anytime"
        "door" in t || "lock" in t -> "Manage your home access"
        "light" in t -> "Adjust your room lighting"
        else -> "Control your connected device"
    }
}

private fun readableState(rawTitle: String, latestState: Map<String, Any>): String {
    val t = rawTitle.lowercase()

    return when {
        "light" in t -> when (latestState["lightOn"]) {
            true -> "On"
            false -> "Off"
            else -> "Tap to check"
        }

        "door" in t || "lock" in t -> when (latestState["locked"]) {
            true -> "Locked"
            false -> "Unlocked"
            else -> "Tap to check"
        }

        "coffee" in t -> when (latestState["isMaking"]) {
            true -> "Brewing"
            false -> "Ready"
            else -> "Tap to check"
        }

        else -> "Tap to check"
    }
}

private fun deviceIconRes(rawTitle: String): Int {
    val t = rawTitle.lowercase()

    return when {
        "light" in t -> R.drawable.lightbulb
        "door" in t || "lock" in t -> R.drawable.door
        "coffee" in t -> R.drawable.coffee_cup
        else -> R.drawable.lightbulb
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

@Preview(showBackground = true, showSystemUi = true)
@Composable
private fun CoffeeDeviceScreenPreview() {
    MaterialTheme {
        DeviceScreen(
            title = "coffee-machine-1",
            uiDefinition = null,
            latestState = mapOf("isMaking" to true),
            error = null,
            onBack = {},
            onAction = {}
        )
    }
}