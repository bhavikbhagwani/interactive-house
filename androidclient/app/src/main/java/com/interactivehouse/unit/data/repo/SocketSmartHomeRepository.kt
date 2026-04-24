package com.interactivehouse.unit.data.repo

import com.interactivehouse.unit.config.ServerConfig
import com.interactivehouse.unit.data.models.Control
import com.interactivehouse.unit.data.models.Device
import com.interactivehouse.unit.data.models.DisabledWhen
import com.interactivehouse.unit.data.models.UiDefinition
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.IOException
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.Socket
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

class SocketSmartHomeRepository(
    private val host: String = ServerConfig.HOST,
    private val port: Int = ServerConfig.PORT,
    private val senderId: String = "android-${UUID.randomUUID().toString().take(8)}"
) : SmartHomeRepository {

    private var socket: Socket? = null
    private var reader: BufferedReader? = null
    private var writer: BufferedWriter? = null
    private val writeMutex = Mutex()

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var readJob: Job? = null

    private val stateFlows = ConcurrentHashMap<String, MutableSharedFlow<Map<String, Any>>>()
    private fun flowFor(deviceId: String) =
        stateFlows.getOrPut(deviceId) { MutableSharedFlow(replay = 1) }

    private val pending = ConcurrentHashMap<String, CompletableDeferred<JSONObject>>()

    private suspend fun sendAndAwait(
        msg: JSONObject,
        responseType: String,
        timeoutMs: Long = 5000
    ): JSONObject {
        val d = CompletableDeferred<JSONObject>()
        pending[responseType] = d

        return try {
            send(msg)
            withTimeout(timeoutMs) {
                d.await()
            }
        } finally {
            pending.remove(responseType)
        }
    }

    private fun closeResources() {
        runCatching { reader?.close() }
        runCatching { writer?.close() }
        runCatching { socket?.close() }

        reader = null
        writer = null
        socket = null
    }

    private suspend fun ensureConnected() {
        val s = socket
        if (s != null && s.isConnected && !s.isClosed) return

        disconnect()

        val newSocket = Socket(host, port)
        socket = newSocket
        reader = BufferedReader(InputStreamReader(newSocket.getInputStream(), Charsets.UTF_8))
        writer = BufferedWriter(OutputStreamWriter(newSocket.getOutputStream(), Charsets.UTF_8))

        log("CONNECTED to $host:$port as $senderId")

        readJob = scope.launch { readLoopNdjson() }
    }

    private suspend fun disconnect() {
        runCatching { readJob?.cancel() }
        readJob = null
        closeResources()
    }

    private fun baseMessage(type: String, payload: JSONObject = JSONObject()): JSONObject {
        return JSONObject()
            .put("type", type)
            .put("sender_id", senderId)
            .put("payload", payload)
    }

    private suspend fun send(msg: JSONObject) {
        ensureConnected()
        val w = writer ?: throw IOException("Writer not ready")

        val line = msg.toString() + "\n"
        writeMutex.withLock {
            w.write(line)
            w.flush()
        }
        log("SEND: $line")
    }

    private suspend fun awaitType(type: String, timeoutMs: Long = 5000): JSONObject {
        val d = CompletableDeferred<JSONObject>()
        pending[type] = d
        return withTimeout(timeoutMs) {
            try {
                d.await()
            } finally {
                pending.remove(type)
            }
        }
    }

    private suspend fun readLoopNdjson() {
        try {
            val r = reader ?: return

            while (currentCoroutineContext().isActive) {
                val line = r.readLine() ?: break
                if (line.isBlank()) continue

                log("RECV: $line")

                val msg = runCatching { JSONObject(line) }.getOrNull() ?: continue
                val type = msg.optString("type", "")

                when (type) {
                    "state_update", "device_state" -> handleStateUpdate(msg)
                    else -> pending[type]?.complete(msg)
                }
            }
        } catch (e: Exception) {
            log("READ LOOP ERROR: ${e.message}")
        } finally {
            closeResources()
            log("DISCONNECTED")
        }
    }

    private suspend fun handleStateUpdate(msg: JSONObject) {
        val payload = msg.optJSONObject("payload") ?: return

        val deviceId =
            payload.optString("deviceId")
                .ifBlank { payload.optString("device_id") }
                .ifBlank { msg.optString("sender_id") }
                .ifBlank { "" }

        val stateObj =
            payload.optJSONObject("state")
                ?: payload.optJSONObject("latestState")

        if (deviceId.isBlank() || stateObj == null) return

        val stateMap = jsonObjectToMap(stateObj)
        log("STATE for $deviceId => $stateMap")
        flowFor(deviceId).emit(stateMap)
    }

    override suspend fun login(email: String, password: String): Boolean {
        log("LOGIN start: host=$host port=$port user=$email")

        val payload = JSONObject()
            .put("email", email)
            .put("password", password)

        return try {
            val okMsg = runCatching {
                sendAndAwait(baseMessage("login", payload), "login_ok", 5000)
            }.getOrNull()

            if (okMsg != null) {
                log("LOGIN ok")
                return true
            }

            val failMsg =
                runCatching { awaitType("login_failed", 500) }.getOrNull()
                    ?: runCatching { awaitType("error", 500) }.getOrNull()

            log("LOGIN not ok: ${failMsg?.optString("type") ?: "no response"}")
            false
        } catch (e: Exception) {
            log("LOGIN exception: ${e::class.java.simpleName}: ${e.message}")
            false
        }
    }

    override suspend fun getDevices(): List<Device> {
        val msg = try {
            sendAndAwait(baseMessage("get_devices"), "device_list", timeoutMs = 4000)
        } catch (e: Exception) {
            val err = runCatching { awaitType("error", timeoutMs = 500) }.getOrNull()
            val reason = err?.optJSONObject("payload")?.optString("message")
                ?: "Server did not respond with device_list."
            throw IOException(reason, e)
        }

        val payload = msg.optJSONObject("payload") ?: JSONObject()
        val devicesArr = payload.optJSONArray("devices") ?: JSONArray()

        val out = mutableListOf<Device>()
        for (i in 0 until devicesArr.length()) {
            val d = devicesArr.optJSONObject(i) ?: continue
            val id = d.optString("deviceId").ifBlank { d.optString("device_id") }
            val type = d.optString("deviceType").ifBlank { d.optString("device_type") }
            if (id.isNotBlank()) out.add(Device(deviceId = id, deviceType = type.ifBlank { id }))
        }
        return out
    }

    override suspend fun getUi(deviceId: String): UiDefinition {
        val msg = try {
            sendAndAwait(
                baseMessage("get_ui", JSONObject().put("deviceId", deviceId)),
                "ui_definition",
                timeoutMs = 4000
            )
        } catch (e: Exception) {
            val err = runCatching { awaitType("error", timeoutMs = 800) }.getOrNull()
            val reason = err?.optJSONObject("payload")?.optString("message")
                ?: "Failed to get UI for $deviceId"
            throw IOException(reason, e)
        }

        val p = msg.optJSONObject("payload") ?: JSONObject()
        log("GET_UI payload for $deviceId = $p")
        val title = p.optString("title").ifBlank { p.optString("deviceType") }.ifBlank { deviceId }

        val stateObj = p.optJSONObject("state") ?: JSONObject()
        val initialState = jsonObjectToMap(stateObj)
        log("GET_UI initialState for $deviceId = $initialState")

        val uiArr = p.optJSONArray("ui") ?: JSONArray()
        val controls = mutableListOf<Control>()


        for (i in 0 until uiArr.length()) {
            val c = uiArr.optJSONObject(i) ?: continue

            val kind = c.optString("type", "button")
            val label = c.optString("label", c.optString("text", ""))
            val action = c.optString("action", "")

            val dwObj = c.optJSONObject("disabledWhen")
            val disabledWhen =
                if (dwObj != null) {
                    val stateKey = dwObj.optString("stateKey")
                        .ifBlank { dwObj.optString("field") }
                        .ifBlank { dwObj.optString("key") }
                    val equals =
                        if (dwObj.has("equals")) dwObj.optBoolean("equals")
                        else dwObj.optBoolean("value", false)

                    if (stateKey.isNotBlank()) DisabledWhen(stateKey = stateKey, equals = equals) else null
                } else null
            val enabled =
                if (c.has("enabled")) c.optBoolean("enabled")
                else null

            controls.add(
                Control(
                    kind = kind,
                    label = label,
                    action = action,
                    disabledWhen = disabledWhen,
                    enabled = enabled
                )
            )
        }

        return UiDefinition(
            title = title,
            controls = controls,
            initialState = initialState
        )
    }

    override fun stateUpdates(deviceId: String): Flow<Map<String, Any>> {
        return flowFor(deviceId).asSharedFlow()
    }

    override suspend fun sendAction(deviceId: String, action: String) {
        val payload = JSONObject()
            .put("deviceId", deviceId)
            .put("action", action)

        send(baseMessage("action", payload))
    }

    override suspend fun triggerScene(sceneId: String) {
        val payload = JSONObject()
            .put("sceneId", sceneId)

        send(baseMessage("trigger_scene", payload))
    }

    override suspend fun sendVoiceCommand(text: String) {
        val payload = JSONObject()
            .put("text", text)

        send(baseMessage("voice_command", payload))
    }

    private fun jsonObjectToMap(obj: JSONObject): Map<String, Any> {
        val map = mutableMapOf<String, Any>()
        val keys = obj.keys()
        while (keys.hasNext()) {
            val k = keys.next()
            val v = obj.opt(k)
            map[k] = when (v) {
                is JSONObject -> jsonObjectToMap(v)
                is JSONArray -> jsonArrayToList(v)
                JSONObject.NULL, null -> ""
                else -> v
            }
        }
        return map
    }

    private fun jsonArrayToList(arr: JSONArray): List<Any> {
        val list = mutableListOf<Any>()
        for (i in 0 until arr.length()) {
            val v = arr.opt(i)
            list.add(
                when (v) {
                    is JSONObject -> jsonObjectToMap(v)
                    is JSONArray -> jsonArrayToList(v)
                    JSONObject.NULL, null -> ""
                    else -> v
                }
            )
        }
        return list
    }

    private fun log(msg: String) {
        android.util.Log.d("SocketRepo", msg)
    }
}
