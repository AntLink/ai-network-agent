<template>
    <div class="view">
        <h1>🗺️ GPS Position</h1>

        <div class="grid">
            <div class="card">
                <h3>📍 Current Position</h3>
                <GPSMap :position="position" />
            </div>

            <div class="card">
                <h3>📡 Satellites</h3>
                <div class="satellite-list">
                    <div v-for="sat in satellites" :key="sat.id" class="satellite-item">
                        <span>ID: {{ sat.id }}</span>
                        <span>Elevation: {{ sat.elevation }}°</span>
                        <span>Azimuth: {{ sat.azimuth }}°</span>
                        <span>SNR: {{ sat.snr }} dB</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="info-panel">
            <div class="info-item">
                <label>Latitude:</label>
                <span>{{ position.lat }}°</span>
            </div>
            <div class="info-item">
                <label>Longitude:</label>
                <span>{{ position.lon }}°</span>
            </div>
            <div class="info-item">
                <label>Altitude:</label>
                <span>{{ position.alt }} m</span>
            </div>
            <div class="info-item">
                <label>Speed:</label>
                <span>{{ position.speed }} km/h</span>
            </div>
        </div>
    </div>
</template>

<script>
import GPSMap from '../components/GPSMap.vue'

export default {
    components: { GPSMap },
    data() {
        return {
            position: { lat: 0, lon: 0, alt: 0, speed: 0 },
            satellites: []
        }
    },
    mounted() {
        this.fetchGPS()
        this.interval = setInterval(this.fetchGPS, 5000)
    },
    beforeUnmount() {
        clearInterval(this.interval)
    },
    methods: {
        async fetchGPS() {
            try {
                const [posRes, satRes] = await Promise.all([
                    fetch('http://localhost:8000/api/v1/gps/position'),
                    fetch('http://localhost:8000/api/v1/gps/satellites')
                ])

                this.position = await posRes.json()
                const satData = await satRes.json()
                this.satellites = satData.satellites || []
            } catch (e) {
                console.error('Failed to fetch GPS:', e)
            }
        }
    }
}
</script>
