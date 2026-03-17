<template>
  <canvas ref="canvasRef" class="wave-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  // 线条颜色（RGB，不含透明度）
  lineColor:  { type: String,  default: '232, 215, 183' },
  // 总线条数
  lineCount:  { type: Number,  default: 60 },
  // 中心最大振幅（px，相对于 canvas 高度的比例）
  amplitude:  { type: Number,  default: 0.13 },
  // 波浪流动速度（越小越慢）
  speed:      { type: Number,  default: 0.00018 },
  // 每条线的水平波长系数（越大越舒展）
  frequency:  { type: Number,  default: 0.0028 },
})

const canvasRef = ref(null)
let rafId = null
let startTime = null

// ── 高清屏适配 ──────────────────────────────────────────
// 将 canvas 的物理像素设为 CSS 尺寸 × dpr，避免模糊
function resize(canvas) {
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  canvas.width  = rect.width  * dpr
  canvas.height = rect.height * dpr
  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
  return rect
}

// ── 波浪函数 ────────────────────────────────────────────
// 每条线 i 的 y 偏移 = 振幅 × 中心权重 × sin(x × 频率 + 时间偏移 + 线相位)
// 中心权重：让中间的线起伏更大，两侧趋近于平
function waveY(x, t, lineIndex, totalLines, canvasH) {
  const maxAmp = canvasH * props.amplitude

  // 中心权重：以线条索引为基础，中间 = 1，边缘 → 0
  // 用 sin 曲线让过渡更柔和
  const norm   = lineIndex / (totalLines - 1)          // 0 ~ 1
  const weight = Math.sin(norm * Math.PI)              // 0 → 1 → 0

  // 每条线有独立相位偏移，形成层叠错落感
  const phase  = lineIndex * 0.22

  // 两个频率叠加，让波形更自然（不是单纯正弦）
  const y = maxAmp * weight * (
    0.65 * Math.sin(x * props.frequency + t + phase) +
    0.35 * Math.sin(x * props.frequency * 1.7 + t * 0.8 + phase * 1.3)
  )
  return y
}

// ── 绘制单帧 ────────────────────────────────────────────
function draw(canvas, ctx, t) {
  const W = canvas.getBoundingClientRect().width
  const H = canvas.getBoundingClientRect().height

  ctx.clearRect(0, 0, W, H)

  const n = props.lineCount

  for (let i = 0; i < n; i++) {
    // 线条在垂直方向均匀分布，集中在中间 60% 区域
    const norm  = i / (n - 1)                          // 0 ~ 1
    const baseY = H * (0.2 + norm * 0.6)               // 20% ~ 80%

    // 透明度：中间线更不透明，边缘更淡，形成"聚焦"感
    const weight  = Math.sin(norm * Math.PI)
    const opacity = 0.04 + weight * 0.22

    ctx.beginPath()
    ctx.strokeStyle = `rgba(${props.lineColor}, ${opacity})`
    ctx.lineWidth   = 0.6

    // 逐点绘制波浪路径
    const step = 4                                     // 每 4px 取一个点，平衡精度与性能
    for (let x = 0; x <= W; x += step) {
      const y = baseY + waveY(x, t, i, n, H)
      if (x === 0) ctx.moveTo(x, y)
      else         ctx.lineTo(x, y)
    }
    ctx.stroke()
  }
}

// ── 动画循环 ────────────────────────────────────────────
// 用 performance.now() 计算相对时间，乘以 speed 控制流速
function loop(ts) {
  if (!startTime) startTime = ts
  const t = (ts - startTime) * props.speed

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  draw(canvas, ctx, t)
  rafId = requestAnimationFrame(loop)
}

// ── resize 监听 ─────────────────────────────────────────
// 窗口尺寸变化时重新设置 canvas 物理像素，防止拉伸变形
let resizeObserver = null

onMounted(() => {
  const canvas = canvasRef.value
  resize(canvas)

  resizeObserver = new ResizeObserver(() => {
    resize(canvas)
  })
  resizeObserver.observe(canvas)

  rafId = requestAnimationFrame(loop)
})

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<style scoped>
.wave-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
