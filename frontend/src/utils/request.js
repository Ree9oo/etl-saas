import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 统一响应格式：{ code, msg, data }
const service = axios.create({
  baseURL: '/api',
  timeout: 60000
})

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = 'Bearer ' + token
    }
    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => {
    const data = response.data
    // 业务成功
    if (data && data.code === 0) {
      return data.data
    }
    // 业务失败（含 401/403 等业务码）
    ElMessage.error(data?.msg || '请求失败')
    return Promise.reject(data)
  },
  (error) => {
    const status = error.response?.status
    const responseData = error.response?.data
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
      ElMessage.error('登录已失效，请重新登录')
    } else {
      ElMessage.error(
        responseData?.msg || responseData?.detail || error.message || '请求失败，请稍后重试'
      )
    }
    return Promise.reject(error)
  }
)

export default service
