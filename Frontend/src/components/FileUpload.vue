<template>
  <div class="file-upload">
    <label class="upload-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    <div
      class="upload-area"
      :class="{ 'drag-over': isDragOver, 'has-file': file }"
      @click="triggerFileInput"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        @change="handleFileChange"
        style="display: none"
      />

      <div v-if="!file" class="upload-placeholder">
        <div class="upload-icon">📁</div>
        <div class="upload-text">
          <p class="main-text">拖拽文件到此处</p>
          <p class="sub-text">或点击选择文件</p>
        </div>
      </div>

      <div v-else class="file-info">
        <div class="file-icon">✅</div>
        <div class="file-details">
          <div class="file-name">{{ file.name }}</div>
          <div class="file-size">{{ formatFileSize(file.size) }}</div>
        </div>
        <button class="remove-btn" @click.stop="removeFile">×</button>
      </div>
    </div>
    <p v-if="hint" class="upload-hint">{{ hint }}</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  required: {
    type: Boolean,
    default: false
  },
  accept: {
    type: String,
    default: '*'
  },
  hint: {
    type: String,
    default: ''
  },
  modelValue: {
    type: File,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const file = ref(props.modelValue)
const isDragOver = ref(false)

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  file.value = newValue
})

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileChange = (event) => {
  const selectedFile = event.target.files[0]
  if (selectedFile) {
    file.value = selectedFile
    emit('update:modelValue', selectedFile)
  }
}

// 处理拖拽进入
const handleDragOver = () => {
  isDragOver.value = true
}

// 处理拖拽离开
const handleDragLeave = () => {
  isDragOver.value = false
}

// 处理文件拖放
const handleDrop = (event) => {
  isDragOver.value = false
  const droppedFile = event.dataTransfer.files[0]
  if (droppedFile) {
    file.value = droppedFile
    emit('update:modelValue', droppedFile)
  }
}

// 移除文件
const removeFile = () => {
  file.value = null
  emit('update:modelValue', null)
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.file-upload {
  margin-bottom: 20px;
}

.upload-label {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #333; /* 深灰色 */
  margin-bottom: 10px;
}

.required {
  color: #dc3545; /* 低饱和红色 */
  margin-left: 4px;
}

.upload-area {
  border: 2px dashed #d0d0d0; /* 浅灰色边框 */
  border-radius: 10px;
  padding: 30px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #4CAF50; /* 豆绿色 */
  background: #f9fdf9; /* 非常浅的绿色 */
}

.upload-area.drag-over {
  border-color: #4CAF50; /* 豆绿色 */
  background: #f0f8f0; /* 浅绿色 */
}

.upload-area.has-file {
  border-color: #4CAF50; /* 豆绿色 */
  background: #f9fdf9; /* 非常浅的绿色 */
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.upload-icon {
  font-size: 48px;
}

.upload-text {
  text-align: center;
}

.main-text {
  font-size: 16px;
  color: #333; /* 深灰色 */
  margin-bottom: 5px;
  font-weight: 500;
}

.sub-text {
  font-size: 14px;
  color: #999; /* 浅灰色 */
}

.file-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.file-icon {
  font-size: 32px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 16px;
  font-weight: 600;
  color: #333; /* 深灰色 */
  margin-bottom: 4px;
}

.file-size {
  font-size: 14px;
  color: #666; /* 中灰色 */
}

.remove-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #dc3545; /* 低饱和红色 */
  color: white;
  border-radius: 50%;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.remove-btn:hover {
  background: #c82333;
  transform: scale(1.1);
}

.upload-hint {
  margin-top: 8px;
  font-size: 13px;
  color: #999; /* 浅灰色 */
}
</style>
