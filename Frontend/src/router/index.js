import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import FullPage from '@/components/FullPage.vue'
import ResultUploadPage from '@/views/ResultUploadPage.vue'
import ResultDetailPage from '@/views/ResultDetailPage.vue'
import ResultDetailView from '@/views/ResultDetailView.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login,
    meta: { title: '登录 - 豆丰智测' }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { title: '注册 - 豆丰智测' }
  },
  {
    path: '/home',
    name: 'Home',
    component: FullPage,
    meta: { title: '豆丰智测 - 大豆产量智能分析系统' }
  },
  {
    path: '/upload',
    name: 'ResultUpload',
    component: ResultUploadPage,
    meta: { title: '即刻估产 - 豆丰智测' }
  },
  {
    path: '/result',
    name: 'ResultList',
    component: ResultDetailPage,
    meta: { title: '地块管理分析 - 豆丰智测' }
  },
  {
    path: '/result/:runId',
    name: 'ResultDetail',
    component: ResultDetailView,
    meta: { title: '分析结果详情 - 豆丰智测' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  next()
})

export default router
