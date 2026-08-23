<template>
    <div class="log-viewer">
        <pre>{{ logs }}</pre>
    </div>
</template>

<script>
export default {
    props: {
        logs: { type: String, default: '' }
    }
}
</script>
