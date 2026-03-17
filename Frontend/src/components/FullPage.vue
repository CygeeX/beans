<template>
  <div class="relative w-full bg-[#f5f5f0]">
    <!-- 固定顶部导航栏 -->
    <nav
      :class="[
        'fixed top-0 left-0 right-0 z-50 transition-all duration-500',
        isScrolled
          ? 'bg-[rgba(26,21,16,0.95)] backdrop-blur-xl shadow-lg'
          : 'bg-transparent'
      ]"
    >
      <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <!-- Logo -->
        <div class="flex items-center space-x-3">
          <img src="/vite.png" alt="Logo" class="h-10 w-auto" />
          <div class="flex flex-col">
            <span class="text-xl font-bold bg-gradient-to-r from-[rgb(227,224,186)] to-[rgb(181,153,78)] bg-clip-text text-transparent">豆丰智测</span>
            <span class="text-xs text-white tracking-wider">大豆估产与决策平台</span>
          </div>
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
            <span class="text-sm">中文</span>
          </button>
         <router-link
  to="/"
  class="px-4 py-2 text-sm text-white/90 hover:text-white transition-colors"
>
  退出登录
</router-link>
         
        </div>
      </div>
    </nav>

    <!-- Section 1: Hero Section -->
    <section id="hero" class="relative w-full h-screen overflow-hidden">
      <!-- 动态背景层 -->
      <div class="absolute inset-0 bg-[#1a1510]">
        <!-- 视频背景 -->
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

        <!-- 图片背景 -->
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
            <button @click="$router.push('/upload')"
              class="px-8 py-3.5 bg-[#4CAF50] hover:bg-[#45a049] text-white font-bold text-base rounded-full transition-all duration-300 shadow-lg hover:shadow-xl hover:scale-105"
            >
              即刻估产
            </button>
            <button @click="$router.push('/result')"
              class="px-8 py-3.5 bg-transparent border-2 border-white/80 hover:border-white text-white font-semibold text-base rounded-full transition-all duration-300 hover:bg-white/10"
            >
              地块管理分析
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
                    'absolute left-0 top-0 h-full bg-[#4CAF50] transition-all',
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
    </section>

    <!-- Section 2: Banner (经销商+农民独家优惠) -->
    <section
      id="banner"
      class="py-20 px-6"
      ref="bannerSection"
      :class="{ 'animate-reveal': bannerVisible }"
    >
      <div class="max-w-7xl mx-auto">
        <div class="bg-[#1a1510] rounded-3xl overflow-hidden flex flex-col lg:flex-row items-center">
          <!-- 左侧文字内容 -->
          <div class="flex-1 p-12 lg:p-16">
            <h2 class="text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
              种植户 + 保险机构双赢方案
            </h2>
            <p class="text-white/70 text-lg mb-8 leading-relaxed">
              为大豆种植户提供精准管理决策，为农业保险机构提供灾情评估与风险定价依据。
            </p>

            <!-- 特性列表 -->
            <div class="flex flex-wrap gap-4 mb-8">
              <div class="flex items-center space-x-2">
                <span class="text-[#FFC107]">✓</span>
                <span class="text-white/80 text-sm">产量热力图生成</span>
              </div>
              <div class="flex items-center space-x-2">
                <span class="text-[#FFC107]">✓</span>
                <span class="text-white/80 text-sm">高低产地块对比</span>
              </div>
            </div>

            <!-- 按钮组 -->
            <div class="flex flex-wrap gap-4">
              <button class="px-8 py-3.5 bg-[#4CAF50] hover:bg-[#45a049] text-white font-bold rounded-full transition-all duration-300 shadow-lg hover:scale-105">
                立即体验
              </button>
              <button class="px-8 py-3.5 bg-transparent border-2 border-white/60 hover:border-white text-white font-semibold rounded-full transition-all duration-300">
                了解技术方案
              </button>
            </div>
          </div>

          <!-- 右侧图片 -->
          <div class="flex-1 relative h-80 lg:h-96 w-full">
            <img
              :src="bannerImage"
              alt="握手合作"
              class="absolute inset-0 w-full h-full object-cover"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Section 3: Features Grid (特征网格) -->
    <section
      id="features"
      class="py-20 px-6 bg-[#2a2520]"
      ref="featuresSection"
      :class="{ 'animate-reveal': featuresVisible }"
    >
      <div class="max-w-7xl mx-auto">
        <!-- 顶部视频/图片预览 -->
        <div class="relative rounded-3xl overflow-hidden mb-16 h-96 lg:h-[500px]">
          <img
            :src="featuresImage"
            alt="农业机械作业"
            class="w-full h-full object-cover"
          />
          <!-- 播放按钮 -->
          <div class="absolute inset-0 flex items-center justify-center">
            <button class="w-20 h-20 bg-white/20 backdrop-blur-sm hover:bg-white/30 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110">
              <span class="text-white text-3xl ml-1">▶</span>
            </button>
          </div>
        </div>

        <!-- 底部三个特性 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="(feature, index) in features"
            :key="index"
            class="group"
          >
            <!-- 图标 -->
            <div class="mb-6">
              <div class="w-12 h-12 bg-[#FFC107] rounded-lg flex items-center justify-center">
                <span class="text-2xl">{{ feature.icon }}</span>
              </div>
            </div>

            <!-- 标题 -->
            <h3 class="text-2xl font-bold text-white mb-4">
              {{ feature.title }}
            </h3>

            <!-- 描述 -->
            <p class="text-white/70 leading-relaxed mb-4">
              {{ feature.description }}
            </p>

            <!-- 链接 -->
            <a href="#" class="text-[#4CAF50] hover:text-[#45a049] font-semibold inline-flex items-center space-x-2 transition-colors">
              <span>了解更多</span>
              <span>→</span>
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 4: Technology (技术特性) -->
    <section
      id="technology"
      class="py-20 px-6 bg-gradient-to-br from-[#1a1510] to-[#2a2520]"
      ref="technologySection"
      :class="{ 'animate-reveal': technologyVisible }"
    >
      <div class="max-w-7xl mx-auto">
        <!-- 顶部标题 -->
        <div class="text-center mb-16">
          <span class="text-[#FFC107] text-sm font-semibold tracking-wider uppercase mb-4 block">
            先进技术，轻量部署
          </span>
          <h2 class="text-4xl lg:text-5xl font-bold text-white leading-tight">
            核心技术亮点
          </h2>
        </div>

        <!-- 技术卡片网格 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div
            v-for="(tech, index) in technologies"
            :key="index"
            class="bg-white/5 backdrop-blur-sm rounded-2xl p-8 hover:bg-white/10 transition-all duration-300 hover:scale-105 border border-white/10"
          >
            <!-- 图标 -->
            <div class="mb-6">
              <div class="w-16 h-16 bg-gradient-to-br from-[#4CAF50] to-[#45a049] rounded-xl flex items-center justify-center">
                <span class="text-3xl">{{ tech.icon }}</span>
              </div>
            </div>

            <!-- 标题 -->
            <h3 class="text-xl font-bold text-white mb-4">
              {{ tech.title }}
            </h3>

            <!-- 描述 -->
            <p class="text-white/70 leading-relaxed text-sm">
              {{ tech.description }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 5: Process/Steps (流程步骤) -->
    <section
      id="process"
      class="py-20 px-6 bg-[#f5f5f0]"
      ref="processSection"
      :class="{ 'animate-reveal': processVisible }"
    >
      <div class="max-w-7xl mx-auto">
        <!-- 顶部标题 -->
        <div class="mb-12">
          <span class="text-[#4CAF50] text-sm font-semibold tracking-wider uppercase mb-4 block">
            四步实现精准估产
          </span>
          <h2 class="text-4xl lg:text-5xl font-bold text-[#1a1510] leading-tight max-w-2xl">
            从数据采集到决策支持的完整流程
          </h2>
        </div>

        <div class="flex flex-col lg:flex-row gap-12 items-center">
          <!-- 左侧步骤列表 -->
          <div class="flex-1 space-y-6">
            <div
              v-for="(step, index) in steps"
              :key="index"
              @click="activeStep = index"
              :class="[
                'cursor-pointer transition-all duration-300 p-6 rounded-2xl',
                activeStep === index
                  ? 'bg-white shadow-2xl scale-105'
                  : 'bg-transparent hover:bg-white/50'
              ]"
            >
              <div class="flex items-start space-x-4">
                <!-- 数字 -->
                <span
                  :class="[
                    'text-5xl font-bold transition-colors',
                    activeStep === index ? 'text-[#4CAF50]' : 'text-gray-300'
                  ]"
                >
                  {{ step.number }}
                </span>

                <!-- 内容 -->
                <div class="flex-1">
                  <h3
                    :class="[
                      'text-2xl font-bold mb-2 transition-colors',
                      activeStep === index ? 'text-[#1a1510]' : 'text-gray-600'
                    ]"
                  >
                    {{ step.title }}
                  </h3>
                  <p
                    v-if="activeStep === index"
                    class="text-gray-600 leading-relaxed"
                  >
                    {{ step.description }}
                  </p>
                </div>
              </div>
            </div>

            <!-- 底部按钮 -->
            <div class="pt-6">
              <button class="px-8 py-3.5 bg-[#4CAF50] hover:bg-[#45a049] text-white font-bold rounded-full transition-all duration-300 shadow-lg hover:scale-105">
                开始使用豆丰智测
              </button>
            </div>
          </div>

          <!-- 右侧图片 -->
          <div class="flex-1 relative">
            <div class="relative rounded-3xl overflow-hidden shadow-2xl">
              <img
                :src="processImage"
                alt="农民协作"
                class="w-full h-auto"
              />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 5: Footer (页脚) -->
    <footer id="footer" class="bg-[#1a1510] text-white py-16 px-6">
      <div class="max-w-7xl mx-auto">
        <!-- 顶部内容区 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 mb-12">
          <!-- Logo 区域 -->
          <div class="lg:col-span-1">
            <div class="mb-6">
              <span class="text-3xl font-bold text-[#4CAF50] tracking-tight block">豆丰智测</span>
              <span class="text-xs text-gray-400 tracking-wider mt-2 block">SOYBEAN YIELD INTELLIGENCE</span>
            </div>
          </div>

          <!-- 链接列 -->
          <div
            v-for="(column, index) in footerLinks"
            :key="index"
            class="space-y-4"
          >
            <h4 class="text-white font-bold text-lg mb-4">
              {{ column.title }}
            </h4>
            <ul class="space-y-3">
              <li v-for="(link, linkIndex) in column.links" :key="linkIndex">
                <a
                  :href="link.href"
                  class="text-white/70 hover:text-white transition-colors text-sm"
                >
                  {{ link.text }}
                </a>
              </li>
            </ul>
          </div>
        </div>

        <!-- 分隔线 -->
        <div class="border-t border-white/10 pt-8">
          <!-- 底部版权和社交媒体 -->
          <div class="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <!-- 版权信息 -->
            <div class="flex flex-wrap items-center gap-4 text-sm text-white/60">
              <span>© 2025 豆丰智测项目组，版权所有。</span>
              <span>项目周期：2025年11月 - 2027年3月</span>
              <a href="#" class="hover:text-white transition-colors">隐私政策</a>
              <a href="#" class="hover:text-white transition-colors">使用条款</a>
              <a href="#" class="hover:text-white transition-colors">Cookie政策</a>
            </div>

            <!-- 社交媒体图标 -->
            <div class="flex items-center space-x-4">
              <a href="#" class="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors">
                <span class="text-white">in</span>
              </a>
              <a href="#" class="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors">
                <span class="text-white">𝕏</span>
              </a>
              <a href="#" class="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors">
                <span class="text-white">f</span>
              </a>
              <a href="#" class="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors">
                <span class="text-white">📷</span>
              </a>
              <a href="#" class="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors">
                <span class="text-white">▶</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// 导入背景资源
import mainbg1 from '../assets/mainbg1.mp4'
import mainbg2 from '../assets/mainbg2.png'
import mainbg3 from '../assets/mainbg3.png'

// 导入其他图片资源（需要替换为实际路径）
import bannerImg from '../assets/dc1e97cf346cf312801954607fd4080b.png'
import featuresImg from '../assets/eb707610ccd3a9eea60ab91d0264726e.png'
import processImg from '../assets/efed7dde7fc6aa934d374320f92c2763.png'

// 导航链接数据
const navLinks = [
  { text: '产品功能', href: '#features' },
  { text: '技术方案', href: '#technology' },
  { text: '使用流程', href: '#process' },
  { text: '用户服务', href: '#audience' },
  { text: '关于我们', href: '#about' }
]

// Hero 背景资源
const backgrounds = [
  { type: 'video', src: mainbg1 },
  { type: 'image', src: mainbg2 },
  { type: 'image', src: mainbg3 }
]

// Hero 内容数据
const heroContent = [
  {
    tag: '多时相田间观测数据支撑',
    title: '多时相田间观测驱动产量估测',
    subtitle: '基于多日期田间观测数据（SPAD、株高、结荚高等）与地块信息，开展大豆产量估测，并生成田块产量热力图、高低产对比分析和管理建议。'
  },
  {
    tag: '多维特征整合分析',
    title: '整合多维特征，支撑产量建模',
    subtitle: '整合 SPAD、株高、结荚高、多日期观测变化特征及地块空间布局信息，为大豆产量估测提供数据支撑。'
  },
  {
    tag: '特征工程与机器学习支撑',
    title: '机器学习大豆估产模型',
    subtitle: '基于机器学习方法开展大豆产量估测，并结合特征工程支持地块级分析与结果展示。'
  }
]

// 底部模块数据
const modules = [
  { title: '田间观测数据支撑' },
  { title: ' 多维特征建模分析' },
  { title: ' 机器学习估产分析' }
]

// Banner 数据
const bannerImage = bannerImg

// Features 数据
const featuresImage = featuresImg
const features = [
  {
    icon: '🗺️',
    title: '产量热力图生成',
    description: '基于多时相表型数据，生成高精度产量热力分布图，直观展示地块产量差异，辅助精准管理。'
  },
  {
    icon: '📊',
    title: '高低产地块对比',
    description: '智能识别高产与低产地块，进行多维度对比分析，为种植决策提供科学依据。'
  },
  {
    icon: '🛡️',
    title: '灾情风险定损',
    description: '为农业保险机构提供灾情评估与风险定价工具，实现快速定损与理赔决策支持。'
  }
]

// Technology 数据
const technologies = [
  {
    icon: '🛰️',
    title: '多时相田间观测',
    description: '支持导入多日期田间观测数据，支撑地块级产量估测与对比分析。'
  },
  {
    icon: '🐳',
    title: 'Docker 容器化部署',
    description: '基于前后端分离与 Docker 封装，便于平台部署、运行与维护。'
  },
  {
    icon: '🧠',
    title: '特征工程支撑建模',
    description: '提取关键变量与时相变化特征，为大豆产量建模提供分析支撑。'
  },
  {
    icon: '🎯',
    title: '决策知识库辅助分析',
    description: '结合田间管理规则与知识库信息，生成地块管理建议和风险提示。'
  }
]

// Process 数据
const processImage = processImg
const steps = [
  {
    number: '01',
    title: '数据采集',
    description: '通过卫星与无人机协同采集多时相表型数据，覆盖光谱、结构、纹理等多维信息。'
  },
  {
    number: '02',
    title: '特征提取',
    description: '自动提取多模态特征，包括植被指数、冠层结构、纹理特征及覆盖度等关键指标。'
  },
  {
    number: '03',
    title: '模型预测',
    description: '运用特征工程与集成模型进行产量预测，生成高精度产量热力分布图。'
  },
  {
    number: '04',
    title: '决策支持',
    description: '为种植户提供管理建议，为保险机构提供风险评估与定损依据。'
  }
]

// Footer 数据
const footerLinks = [
  {
    title: '产品功能',
    links: [
      { text: '产量热力图生成', href: '#' },
      { text: '高低产地块对比', href: '#' },
      { text: '灾情风险定损', href: '#' },
      { text: '地块管理分析', href: '#' }
    ]
  },
  {
    title: '技术方案',
    links: [
      { text: '多时相田间观测协同', href: '#' },
      { text: '特征工程算法', href: '#' },
      { text: '集成模型预测', href: '#' },
      { text: 'Docker 容器化部署', href: '#' }
    ]
  },
  {
    title: '用户服务',
    links: [
      { text: '种植户解决方案', href: '#' },
      { text: '保险机构服务', href: '#' },
      { text: '技术支持', href: '#' },
      { text: '使用文档', href: '#' }
    ]
  },
  {
    title: '关于我们',
    links: [
      { text: '项目介绍', href: '#' },
      { text: '团队成员', href: '#' },
      { text: '联系我们', href: '#' },
      { text: '合作伙伴', href: '#' }
    ]
  }
]

// 响应式状态
const activeIndex = ref(0)
const progress = ref(0)
const isScrolled = ref(false)
const activeStep = ref(2) // 默认高亮第3步

// Scroll Reveal 状态
const bannerVisible = ref(false)
const featuresVisible = ref(false)
const technologyVisible = ref(false)
const processVisible = ref(false)

// Refs
const bannerSection = ref(null)
const featuresSection = ref(null)
const technologySection = ref(null)
const processSection = ref(null)

let progressInterval = null
let observer = null

// 滚动监听
const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

// 切换模块
const switchModule = (index) => {
  if (index === activeIndex.value) return

  activeIndex.value = index
  progress.value = 0

  if (progressInterval) {
    clearInterval(progressInterval)
  }
  startProgress()
}

// 启动进度条动画
const startProgress = () => {
  const duration = 5000
  const interval = 50
  const increment = (100 / duration) * interval

  progressInterval = setInterval(() => {
    progress.value += increment

    if (progress.value >= 100) {
      progress.value = 100
      clearInterval(progressInterval)

      setTimeout(() => {
        activeIndex.value = (activeIndex.value + 1) % modules.length
        progress.value = 0
        startProgress()
      }, 300)
    }
  }, interval)
}

// Intersection Observer 设置
const setupObserver = () => {
  const options = {
    threshold: 0.2,
    rootMargin: '0px 0px -100px 0px'
  }

  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        if (entry.target === bannerSection.value) {
          bannerVisible.value = true
        } else if (entry.target === featuresSection.value) {
          featuresVisible.value = true
        } else if (entry.target === technologySection.value) {
          technologyVisible.value = true
        } else if (entry.target === processSection.value) {
          processVisible.value = true
        }
      }
    })
  }, options)

  if (bannerSection.value) observer.observe(bannerSection.value)
  if (featuresSection.value) observer.observe(featuresSection.value)
  if (technologySection.value) observer.observe(technologySection.value)
  if (processSection.value) observer.observe(processSection.value)
}

// 生命周期
onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  startProgress()
  setupObserver()

  // 平滑滚动
  document.documentElement.style.scrollBehavior = 'smooth'
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  if (progressInterval) {
    clearInterval(progressInterval)
  }
  if (observer) {
    observer.disconnect()
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
  background-color: #4CAF50;
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

/* Scroll Reveal 动画 */
.animate-reveal {
  animation: reveal 0.8s ease-out forwards;
}

@keyframes reveal {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 字体优化 */
* {
  font-family: system-ui, -apple-system, 'Microsoft YaHei', 'PingFang SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 平滑滚动 */
html {
  scroll-behavior: smooth;
}
</style>
