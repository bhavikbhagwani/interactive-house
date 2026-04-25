package com.interactivehouse.unit.ui.voice

import com.interactivehouse.unit.data.models.Device

class VoiceCommandProcessor {

    fun process(
        text: String,
        devices: List<Device>,
        onScene: (String) -> Unit,
        onDeviceAction: (deviceId: String, action: String) -> Unit,
        onError: (String) -> Unit
    ) {
        val command = normalize(text)

        when {
            command.contains("good night") -> {
                onScene("good_night")
            }

            command.contains("good morning") -> {
                onScene("good_morning")
            }

            command.contains("turn on light") || command.contains("turn on led") -> {
                handleDevice(devices, "light", "ON", onDeviceAction, onError)
            }

            command.contains("turn off light") || command.contains("turn off led") -> {
                handleDevice(devices, "light", "OFF", onDeviceAction, onError)
            }

            command.contains("turn on fan") -> {
                handleDevice(devices, "fan", "ON", onDeviceAction, onError)
            }

            command.contains("turn off fan") -> {
                handleDevice(devices, "fan", "OFF", onDeviceAction, onError)
            }

            command.contains("open door")
                    || command.contains("unlock door") -> {
                handleDevice(devices, "door", "UNLOCK", onDeviceAction, onError)
            }

            command.contains("close door")
                    || command.contains("lock door") -> {
                handleDevice(devices, "door", "LOCK", onDeviceAction, onError)
            }

            command.contains("make coffee")
                    || command.contains("start coffee")
                    || command.contains("coffee") -> {
                handleDevice(devices, "coffee", "MAKE", onDeviceAction, onError)
            }

            else -> {
                onError("Unknown command: $text")
            }
        }
    }
    private fun handleDevice(
        devices: List<Device>,
        keyword: String,
        action: String,
        onDeviceAction: (String, String) -> Unit,
        onError: (String) -> Unit
    ) {
        val device = devices.firstOrNull {
            it.deviceType.lowercase().contains(keyword) ||
                    it.deviceId.lowercase().contains(keyword)
        }

        if (device != null) {
            onDeviceAction(device.deviceId, action)
        } else {
            onError("No $keyword device found")
        }
    }

    private fun normalize(text: String): String {
        return text
            .lowercase()
            .replace(Regex("\\bthe\\b"), "")
            .replace(Regex("\\s+"), " ")
            .trim()
    }
}
