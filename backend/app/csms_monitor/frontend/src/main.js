import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './styles/main.css'

const routes = [
    { path: '/', redirect: '/spectrum' },
    { path: '/spectrum', component: () => import('./views/Spectrum.vue') },
    { path: '/system', component: () => import('./views/System.vue') },
    { path: '/gps', component: () => import('./views/GPS.vue') },
    { path: '/logs', component: () => import('./views/Logs.vue') },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
