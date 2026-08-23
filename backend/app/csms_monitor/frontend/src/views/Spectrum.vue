<template>
    <div class="view">
        <h1>📊 Spectrum Monitor</h1>
        <div class="controls">
            <label>Start Freq (MHz):</label>
            <input type="number" v-model="startFreq" min="0.09" max="8500" step="1">

            <label>Stop Freq (MHz):</label>
            <input type="number" v-model="stopFreq" min="0.09" max="8500" step="1">

            <button @click="updateSweep">Update Sweep</button>
            <button @click="toggleLive" :class="live ? 'active' : ''">
                {{ live ? '⏸ Pause' : '▶ Live' }}
            </button>
        </div>

        <div class="chart-container">
            <SpectrumChart :data="spectrumData" :startFreq="startFreq" :stopFreq="stopFreq" />
        </div>

        <div class="info-panel">
            <div class="info-item">
                <label>Current Frequency:</label>
                <span>{{ currentFreq }} MHz</span>
            </div>
            <div class="info-item">
                <label>Power Level:</label>
                <span>{{ powerLevel }} dBm</span>
            </div>
            <div class="info-item">
                <label>Span:</label>
                <span>{{ stopFreq - startFreq }} MHz</span>
            </div>
        </div>
    </div>
</template>

<script>
import SpectrumChart from '../components/SpectrumChart.vue'

export default {
    components: { SpectrumChart },
    data() {
        return {
            startFreq: 88,
            stopFreq: 108,
            spectrumData: [],
            currentFreq: 0,
            powerLevel: 0,
            live: false,
            interval: null
        }
    },
    mounted() {
        this.$root.$on('ws-message', this.handleWSMessage)
    },
    beforeUnmount() {
        this.$root.$off('ws-message', this.handleWSMessage)
        if (this.interval) clearInterval(this.interval)
    },
    methods: {
        handleWSMessage(data) {
            if (data.type === 'spectrum') {
                this.spectrumData = data.data
                this.currentFreq = data.currentFreq
                this.powerLevel = data.powerLevel
            }
        },
        async updateSweep() {
            const startHz = this.startFreq * 1000000
            const stopHz = this.stopFreq * 1000000

            await fetch(`http://localhost:8000/api/v1/scpi/sweep/start/${startHz}`, { method: 'POST' })
            await fetch(`http://localhost:8000/api/v1/scpi/sweep/stop/${stopHz}`, { method: 'POST' })
        },
        toggleLive() {
            this.live = !this.live
            if (this.live) {
                this.interval = setInterval(this.fetchSpectrum, 100)
            } else {
                clearInterval(this.interval)
            }
        },
        async fetchSpectrum() {
            try {
                const res = await fetch('http://localhost:8000/api/v1/scpi/sweep/data')
                const data = await res.json()
                this.spectrumData = data.data
            } catch (e) {
                console.error('Failed to fetch spectrum:', e)
            }
        }
    }
}
</script>
