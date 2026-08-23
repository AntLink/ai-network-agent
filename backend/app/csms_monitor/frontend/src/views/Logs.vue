<template>
    <div class="view">
        <h1>📜 System Logs</h1>

        <div class="controls">
            <label>Lines:</label>
            <input type="number" v-model="lines" min="10" max="500" step="10">
            <button @click="fetchLogs">Refresh</button>
            <button @click="autoRefresh" :class="auto ? 'active' : ''">
                {{ auto ? '⏸ Stop Auto' : '▶ Auto Refresh' }}
            </button>
        </div>

        <div class="log-container">
            <LogViewer :logs="logs" />
        </div>
    </div>
</template>

<script>
import LogViewer from '../components/LogViewer.vue'

export default {
    components: { LogViewer },
    data() {
        return {
            logs: '',
            lines: 100,
            auto: false,
            interval: null
        }
    },
    mounted() {
        this.fetchLogs()
    },
    beforeUnmount() {
        if (this.interval) clearInterval(this.interval)
    },
    methods: {
        async fetchLogs() {
            try {
                const res = await fetch(`http://localhost:8000/api/v1/system/logs/${this.lines}`)
                const data = await res.json()
                this.logs = data.logs
            } catch (e) {
                console.error('Failed to fetch logs:', e)
            }
        },
        autoRefresh() {
            this.auto = !this.auto
            if (this.auto) {
                this.interval = setInterval(this.fetchLogs, 2000)
            } else {
                clearInterval(this.interval)
            }
        }
    }
}
</script>
