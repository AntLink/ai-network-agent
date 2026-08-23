<template>
    <div class="spectrum-chart">
        <canvas ref="chart"></canvas>
    </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
    props: {
        data: { type: Array, default: () => [] },
        startFreq: { type: Number, default: 88 },
        stopFreq: { type: Number, default: 108 }
    },
    data() {
        return {
            chart: null
        }
    },
    mounted() {
        this.initChart()
    },
    watch: {
        data: {
            handler(newData) {
                this.updateChart(newData)
            },
            deep: true
        }
    },
    methods: {
        initChart() {
            const ctx = this.$refs.chart.getContext('2d')
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Power (dBm)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: { display: true, text: 'Frequency (MHz)' }
                        },
                        y: {
                            title: { display: true, text: 'Power (dBm)' }
                        }
                    },
                    animation: { duration: 0 }
                }
            })
        },
        updateChart(data) {
            if (!this.chart || !data.length) return

            const labels = data.map((_, i) => {
                const freq = this.startFreq + (i * (this.stopFreq - this.startFreq) / data.length)
                return freq.toFixed(2)
            })

            this.chart.data.labels = labels
            this.chart.data.datasets[0].data = data
            this.chart.update('none')
        }
    }
}
</script>
