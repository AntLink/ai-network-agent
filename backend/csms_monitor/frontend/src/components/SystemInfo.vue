<template>
    <div class="system-info">
        <div v-for="(status, name) in services" :key="name" class="service-item">
            <span class="service-name">{{ name }}</span>
            <span :class="status === 'running' ? 'status-ok' : 'status-error'">
                {{ status }}
            </span>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        services: { type: Object, default: () => ({}) }
    }
}
</script>
