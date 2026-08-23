<template>
    <div class="view">
        <h1>💻 System Dashboard</h1>

        <div class="grid">
            <div class="card">
                <h3>🔧 Services</h3>
                <SystemInfo :services="services" />
            </div>

            <div class="card">
                <h3>📈 System Info</h3>
                <div class="info-content">
                    <pre>{{ systemInfo }}</pre>
                </div>
            </div>

            <div class="card">
                <h3>⚙️ Controls</h3>
                <div class="controls">
                    <button @click="startCsmsd" class="btn-success">Start CSMSD</button>
                    <button @click="stopCsmsd" class="btn-danger">Stop CSMSD</button>
                    <button @click="refreshInfo" class="btn-primary">Refresh</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import SystemInfo from '../components/SystemInfo.vue'

export default {
    components: { SystemInfo },
    data() {
        return {
            services: {},
            systemInfo: ''
        }
    },
    mounted() {
        this.refreshInfo()
    },
    methods: {
        async refreshInfo() {
            try {
                const [servicesRes, infoRes] = await Promise.all([
                    fetch('http://localhost:8000/api/v1/system/services'),
                    fetch('http://localhost:8000/api/v1/system/info')
                ])

                this.services = await servicesRes.json()
                const info = await infoRes.json()
                this.systemInfo = JSON.stringify(info, null, 2)
            } catch (e) {
                console.error('Failed to fetch system info:', e)
            }
        },
        async startCsmsd() {
            await fetch('http://localhost:8000/api/v1/system/csmsd/start', { method: 'POST' })
            setTimeout(this.refreshInfo, 2000)
        },
        async stopCsmsd() {
            await fetch('http://localhost:8000/api/v1/system/csmsd/stop', { method: 'POST' })
            setTimeout(this.refreshInfo, 2000)
        }
    }
}
</script>
