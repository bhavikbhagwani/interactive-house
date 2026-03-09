package com.interactivehouse.unit.data.models

data class UiDefinition(
    val title: String,
    val controls: List<Control>,
    val initialState: Map<String, Any> = emptyMap()
)

data class Control(
    val kind: String,           // "button"
    val label: String,          // "ON", "OFF", "LOCK", "MAKE"
    val action: String,         // what we send in action payload
    val disabledWhen: DisabledWhen? = null,
    val enabled: Boolean? = null
)

data class DisabledWhen(
    val stateKey: String,       // e.g. "isMaking"
    val equals: Boolean
)