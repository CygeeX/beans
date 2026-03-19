// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 训练模型
 * @param {FormData} formData - 包含 ground, yield_xlsx, layout 的表单数据
 * @returns {Promise} 返回训练结果
 */
export async function trainModel(formData) {
<<<<<<< HEAD
  // 添加超时控制
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 800000); // 800秒超时
  
  try {
    const response = await fetch(`${API_BASE_URL}/train`, {
      method: 'POST',
      body: formData,
      signal: controller.signal  // 添加 signal
    });

    clearTimeout(timeoutId);  // 请求完成，清除超时

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }));
      throw new Error(error.detail || `HTTP错误: ${response.status}`);
    }

    const result = await response.json();
=======
  try {
    const response = await fetch(`${API_BASE_URL}/train`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '训练失败')
    }

    const result = await response.json()
>>>>>>> 1a568c4c39025495d55649b0d6763f5b7606ab85

    // 保存到历史记录
    saveToHistory({
      runId: result.run_id,
      type: 'train',
      time: new Date().toLocaleString('zh-CN'),
      status: 'completed',
      files: result.files || [
        { name: '训练结果报告.xlsx', filename: 'train_result.xlsx' },
        { name: '模型参数.csv', filename: 'model_params.csv' }
      ],
      summary: result.summary || null
<<<<<<< HEAD
    });

    return result;
  } catch (error) {
    clearTimeout(timeoutId);  // 发生错误也清除超时
    
    // 处理超时错误
    if (error.name === 'AbortError') {
      console.error('训练超时：请求超过120秒');
      throw new Error('训练时间过长，请稍后重试或检查服务器状态');
    }
    
    console.error('训练模型失败:', error);
    throw error;
=======
    })

    return result
  } catch (error) {
    console.error('训练模型失败:', error)
    throw error
>>>>>>> 1a568c4c39025495d55649b0d6763f5b7606ab85
  }
}

/**
 * 预测产量
 * @param {FormData} formData - 包含 ground, layout 的表单数据
 * @returns {Promise} 返回预测结果
 */
export async function predictYield(formData) {
  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '预测失败')
    }

    const result = await response.json()

    // 保存到历史记录
    saveToHistory({
      runId: result.run_id,
      type: 'predict',
      time: new Date().toLocaleString('zh-CN'),
      status: 'completed',
      files: result.files || [
        { name: '预测结果报告.xlsx', filename: 'predict_result.xlsx' },
        { name: '详细分析数据.csv', filename: 'analysis_data.csv' }
      ],
      summary: result.summary || {
        avgYield: 2350,
        maxBlock: 'A3',
        maxYield: 2680,
        minBlock: 'B7',
        minYield: 2120
      }
    })

    return result
  } catch (error) {
    console.error('预测产量失败:', error)
    throw error
  }
}

/**
 * 下载结果文件
 * @param {string} runId - 任务ID
 * @param {string} filename - 文件名
 */
export async function downloadResult(runId, filename) {
  try {
    const response = await fetch(`${API_BASE_URL}/result/${runId}/${filename}`)

    if (!response.ok) {
      throw new Error('文件下载失败')
    }

    // 创建下载链接
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载文件失败:', error)
    throw error
  }
}

/**
 * 保存分析记录到本地存储
 * @param {Object} record - 分析记录
 */
function saveToHistory(record) {
  const history = JSON.parse(localStorage.getItem('analysisHistory') || '[]')
  history.unshift(record)

  // 只保留最近 20 条记录
  if (history.length > 20) {
    history.splice(20)
  }

  localStorage.setItem('analysisHistory', JSON.stringify(history))
}

/**
 * 健康检查
 * @returns {Promise} 返回健康状态
 */
export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    return await response.json()
  } catch (error) {
    console.error('健康检查失败:', error)
    throw error
  }
}
