import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import ElementPlus from 'element-plus'
import App from './App.vue'
import router from './router'



const app = createApp(App)

// element-plus icons
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import axios from "axios";
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
