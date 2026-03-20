// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 训练模型
 * @param {FormData} formData - 包含 ground, yield_xlsx, layout 的表单数据
 * @returns {Promise} 返回训练结果
 */
export async function trainModel(formData) {
  // 设置25分钟超时（1500秒）
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 1500000); // 1500秒 = 25分钟
  
  try {
    const response = await fetch(`${API_BASE_URL}/train`, {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }));
      throw new Error(error.detail || `HTTP错误: ${response.status}`);
    }

    const result = await response.json();

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
    });

    return result;
    
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      console.error('训练超时：25分钟仍未完成');
      throw new Error('训练时间过长（超过25分钟），建议使用历史记录查看或联系管理员');
    }
    
    console.error('训练模型失败:', error);
    throw error;
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
