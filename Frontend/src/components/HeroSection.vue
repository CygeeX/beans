<template>
  <div class="relative w-full h-screen overflow-hidden">
    <!-- 动态背景层 -->
    <div class="absolute inset-0 bg-[#1a1510]">
      <!-- 视频背景 (activeIndex === 0) -->
      <transition name="fade">
        <video
          v-if="activeIndex === 0"
          :key="backgrounds[0].src"
          class="absolute inset-0 w-full h-full object-cover"
          autoplay
          loop
          muted
          playsinline
        >
          <source :src="backgrounds[0].src" type="video/mp4" />
        </video>
      </transition>

      <!-- 图片背景 (activeIndex === 1, 2) -->
      <transition name="fade">
        <div
          v-if="activeIndex !== 0"
          :key="backgrounds[activeIndex].src"
          class="absolute inset-0 w-full h-full bg-cover bg-center"
          :style="{ backgroundImage: `url(${backgrounds[activeIndex].src})` }"
        ></div>
      </transition>

      <!-- 深色遮罩 -->
      <div class="absolute inset-0 bg-black/40"></div>
    </div>

    <!-- 顶部导航栏 -->
    <nav
      :class="[
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        isScrolled ? 'bg-[#231f20]' : 'bg-transparent'
      ]"
    >
      <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <!-- Logo -->
        <div class="flex items-center space-x-2">
          <span class="text-xs text-gray-400 tracking-wider">THE CLIMATE</span>
          <span class="text-xl font-bold text-white tracking-tight">FIELDVIEW</span>
        </div>

        <!-- 中间导航链接 -->
        <div class="hidden lg:flex items-center space-x-8">
          <a
            v-for="link in navLinks"
            :key="link.text"
            :href="link.href"
            class="nav-link relative text-sm text-white/90 hover:text-white transition-colors duration-300"
          >
            {{ link.text }}
          </a>
        </div>

        <!-- 右侧操作区 -->
        <div class="flex items-center space-x-4">
          <button class="text-white/80 hover:text-white transition-colors">
            <span class="text-sm">搜索</span>
          </button>
          <button class="flex items-center space-x-1 text-white/80 hover:text-white transition-colors">
            <span class="text-xs">🇨🇳</span>
            <span class="text-sm">EN</span>
          </button>
          <button class="px-4 py-2 text-sm text-white/90 hover:text-white transition-colors">
            Log in
          </button>
          <button class="px-5 py-2 bg-[#eab308] hover:bg-[#d9a307] text-black font-semibold text-sm rounded-full transition-all duration-300">
            Create Account
          </button>
        </div>
      </div>
    </nav>

    <!-- Hero 内容区 -->
    <div class="relative z-10 h-full flex flex-col justify-between pt-24 pb-16 px-6">
      <div class="max-w-7xl mx-auto w-full flex-1 flex flex-col justify-center">
        <!-- 小标签 -->
        <div class="mb-6">
          <span class="text-xs text-white/70 tracking-widest uppercase">
            {{ heroContent[activeIndex].tag }}
          </span>
        </div>

        <!-- 主标题 -->
        <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold text-white leading-tight mb-6 max-w-3xl">
          {{ heroContent[activeIndex].title }}
        </h1>

        <!-- 副标题 -->
        <p class="text-lg md:text-xl text-white/80 mb-10 max-w-2xl leading-relaxed">
          {{ heroContent[activeIndex].subtitle }}
        </p>

        <!-- 按钮组 -->
        <div class="flex flex-wrap gap-4">
          <button
            class="px-8 py-3.5 bg-[#eab308] hover:bg-[#d9a307] text-black font-bold text-base rounded-full transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105"
          >
            寻找计划
          </button>
          <button
            class="px-8 py-3.5 bg-transparent border-2 border-white/80 hover:border-white text-white font-semibold text-base rounded-full transition-all duration-300 hover:bg-white/10"
          >
            了解更多信息
          </button>
        </div>
      </div>

      <!-- 底部模块进度条 -->
      <div class="max-w-7xl mx-auto w-full">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="(module, index) in modules"
            :key="index"
            @click="switchModule(index)"
            class="cursor-pointer group"
          >
            <!-- 进度条容器 -->
            <div class="relative h-0.5 bg-white/20 mb-4 overflow-hidden">
              <!-- 进度条填充 -->
              <div
                :class="[
                  'absolute left-0 top-0 h-full bg-[#eab308] transition-all',
                  activeIndex === index ? 'animate-progress' : 'w-0'
                ]"
                :style="{ width: activeIndex === index ? `${progress}%` : '0%' }"
              ></div>
            </div>

            <!-- 模块标题 -->
            <h3
              :class="[
                'text-base md:text-lg font-semibold transition-colors duration-300',
                activeIndex === index ? 'text-white' : 'text-white/60 group-hover:text-white/80'
              ]"
            >
              {{ module.title }}
            </h3>
          </div>
        </div>
      </div>
    </div>

    <!-- 右下角控制区 -->
    <div class="absolute bottom-8 right-8 z-20 flex items-center space-x-4">
      <span class="text-white/70 text-sm">倒带</span>
      <div class="flex space-x-2">
        <button class="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors">
          <span class="text-white text-xs">⏸</span>
        </button>
        <button class="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors">
          <span class="text-white text-xs">🔊</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

// 导入背景资源（Vite 会正确处理这些路径）
import mainbg1 from '../assets/mainbg1.mp4'
import mainbg2 from '../assets/mainbg2.png'
import mainbg3 from '../assets/mainbg3.png'

// 导航链接数据
const navLinks = [
  { text: '我们的解决方案', href: '#solutions' },
  { text: '定价', href: '#pricing' },
  { text: '合作伙伴', href: '#partners' },
  { text: '服务支持', href: '#support' },
  { text: '资源', href: '#resources' }
]

// 背景资源数据（视频/图片）
const backgrounds = [
  { type: 'video', src: mainbg1 },
  { type: 'image', src: mainbg2 },
  { type: 'image', src: mainbg3 }
]

// Hero 内容数据
const heroContent = [
  {
    tag: '赋能农民的未来',
    title: '利用你的数据最大化效果',
    subtitle: '我们能够帮助世界各地的农民，让所能够提升可持续性。'
  },
  {
    tag: '数据驱动决策',
    title: '精准农业的智能洞察',
    subtitle: '通过先进的数据分析，帮助您做出更明智的农业决策。'
  },
  {
    tag: '创新技术引领',
    title: '革新传统农业模式',
    subtitle: '运用前沿科技，推动农业生产力和可持续发展。'
  }
]

// 底部模块数据
const modules = [
  { title: '赋能农民' },
  { title: '数据驱动洞察' },
  { title: '创新农业技术' }
]

// 响应式状态
const activeIndex = ref(0)
const progress = ref(0)
const isScrolled = ref(false)
let progressInterval = null
let animationFrame = null

// 滚动监听
const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

// 切换模块
const switchModule = (index) => {
  if (index === activeIndex.value) return

  activeIndex.value = index
  progress.value = 0

  // 重置进度动画
  if (progressInterval) {
    clearInterval(progressInterval)
  }
  startProgress()
}

// 启动进度条动画
const startProgress = () => {
  const duration = 5000 // 5秒
  const interval = 50 // 每50ms更新一次
  const increment = (100 / duration) * interval

  progressInterval = setInterval(() => {
    progress.value += increment

    if (progress.value >= 100) {
      progress.value = 100
      clearInterval(progressInterval)

      // 自动切换到下一个模块
      setTimeout(() => {
        activeIndex.value = (activeIndex.value + 1) % modules.length
        progress.value = 0
        startProgress()
      }, 300)
    }
  }, interval)
}

// 生命周期
onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  startProgress()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  if (progressInterval) {
    clearInterval(progressInterval)
  }
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
  }
})
</script>

<style scoped>
/* 导航链接悬停下划线效果 */
.nav-link::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background-color: #eab308;
  transition: width 0.3s ease;
}

.nav-link:hover::after {
  width: 100%;
}

/* 背景淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.8s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
}

/* 进度条动画 */
@keyframes progress {
  from {
    width: 0%;
  }
  to {
    width: 100%;
  }
}

.animate-progress {
  animation: progress 5s linear;
}

/* 字体优化 */
* {
  font-family: system-ui, -apple-system, 'Microsoft YaHei', 'PingFang SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
