<template>
    <div class="gps-map" ref="mapContainer"></div>
</template>

<script>
import L from 'leaflet'

export default {
    props: {
        position: { type: Object, default: () => ({ lat: 0, lon: 0 }) }
    },
    data() {
        return {
            map: null,
            marker: null
        }
    },
    mounted() {
        this.initMap()
    },
    watch: {
        position: {
            handler(newPos) {
                this.updateMarker(newPos)
            },
            deep: true
        }
    },
    methods: {
        initMap() {
            this.map = L.map(this.$refs.mapContainer).setView([0, 0], 2)

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map)

            this.marker = L.marker([0, 0]).addTo(this.map)
        },
        updateMarker(pos) {
            if (this.marker && pos.lat && pos.lon) {
                this.marker.setLatLng([pos.lat, pos.lon])
                this.map.setView([pos.lat, pos.lon], 15)
            }
        }
    }
}
</script>
