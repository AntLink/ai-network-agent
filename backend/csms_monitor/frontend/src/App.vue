<template>
    <div class="app">
        <nav class="sidebar">
            <div class="logo">
                <h2>📡 CSMS Monitor</h2>
            </div>
            <ul>
                <li><router-link to="/spectrum">📊 Spectrum</router-link></li>
                <li><router-link to="/system">💻 System</router-link></li>
                <li><router-link to="/gps">🗺️ GPS</router-link></li>
                <li><router-link to="/logs">📜 Logs</router-link></li>
            </ul>
            <div class="status">
                <span :class="connected ? 'online' : 'offline'">
                    {{ connected ? '● Connected' : '● Disconnected' }}
                </span>
            </div>
        </nav>
        <main class="content">
            <router-view />
        </main>
    </div>
</template>

<script>
export default {
    data() {
        return {
            connected: false,
            ws: null
        }
    },
    mounted() {
        this.connectWebSocket()
    },
    methods: {
        connectWebSocket() {
            const wsUrl = `ws://${window.location.hostname}:8000/ws`
            this.ws = new WebSocket(wsUrl)

            this.ws.onopen = () => {
                this.connected = true
            }

            this.ws.onclose = () => {
                this.connected = false
                setTimeout(() => this.connectWebSocket(), 3000)
            }

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data)
                this.$root.$emit('ws-message', data)
            }
        }
    }
}
</script>
