<template>
  <div class="page-card">
    <el-card>
      <template #header>
        <div class="hd">
          <span>执行日志</span>
          <div>
            <el-select v-model="filter.status" style="width: 130px; margin-right: 8px" placeholder="状态" clearable @change="load">
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="运行中" value="running" />
            </el-select>
            <el-button :icon="Refresh" @click="load">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="task_name" label="任务" min-width="140" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
              {{ row.status === 'success' ? '成功' : row.status === 'failed' ? '失败' : '运行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rows" label="同步行数" width="100" />
        <el-table-column prop="duration" label="耗时(s)" width="100" />
        <el-table-column label="开始时间" min-width="160">
          <template #default="{ row }">{{ fmtTime(row.started_at) }}</template>
        </el-table-column>
        <el-table-column label="错误信息" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.error || '-' }}</template>
        </el-table-column>
        <el-table-column label="详情" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="View" @click="show(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pg"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="load"
        layout="total, prev, pager, next"
      />
    </el-card>

    <el-dialog v-model="detail" title="执行详情" width="680px">
      <div class="detail-head">
        <div>
          <span class="detail-label">执行任务</span>
          <strong>{{ current.task_name || '-' }}</strong>
        </div>
        <el-tag :type="statusType(current.status)">{{ statusText(current.status) }}</el-tag>
      </div>

      <div class="detail-grid">
        <div class="detail-item">
          <span>同步行数</span>
          <strong>{{ current.rows ?? 0 }} 行</strong>
        </div>
        <div class="detail-item">
          <span>执行耗时</span>
          <strong>{{ current.duration ?? 0 }} 秒</strong>
        </div>
        <div class="detail-item">
          <span>开始时间</span>
          <strong>{{ fmtTime(current.started_at) }}</strong>
        </div>
        <div class="detail-item">
          <span>完成时间</span>
          <strong>{{ fmtTime(current.finished_at) }}</strong>
        </div>
      </div>

      <div v-if="current.status === 'failed'" class="error-panel">
        <div class="error-title">
          <span class="error-dot"></span>
          <strong>执行未完成</strong>
        </div>
        <p class="friendly-error">{{ friendlyError(current.error) }}</p>
        <details v-if="current.error" class="technical-error">
          <summary>查看技术详情</summary>
          <pre>{{ current.error }}</pre>
        </details>
      </div>
      <el-result v-else-if="current.status === 'success'" icon="success" title="同步执行成功" sub-title="数据已完成同步" />
      <el-result v-else icon="info" title="任务正在执行" sub-title="请稍后刷新日志查看最终结果" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh, View } from '@element-plus/icons-vue'
import request from '../utils/request'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filter = ref({ status: '' })
const detail = ref(false)
const current = ref({})

const fmtTime = (t) => (t ? t.replace('T', ' ').slice(0, 19) : '-')
const statusText = (status) => ({ success: '成功', failed: '失败', running: '运行中' }[status] || '未知')
const statusType = (status) => ({ success: 'success', failed: 'danger', running: 'warning' }[status] || 'info')

const friendlyError = (error = '') => {
  const message = error.toLowerCase()
  if (message.includes('incorrect table name') || message.includes('table name')) {
    return '源表名或目标表名不正确，请检查表名是否为空、是否包含特殊字符。'
  }
  if (message.includes('doesn\'t exist') || message.includes('does not exist')) {
    return '同步涉及的数据表不存在，请确认源表和目标表名称。'
  }
  if (message.includes('duplicate') || message.includes('already exists')) {
    return '目标数据中存在重复记录，请检查目标表的唯一约束或改用清空后写入。'
  }
  if (message.includes('connection refused') || message.includes('cannot connect') || message.includes('10061')) {
    return '无法连接数据库，请检查数据库服务、主机地址和端口是否正确。'
  }
  if (message.includes('timeout') || message.includes('timed out')) {
    return '同步执行超时，请检查网络、数据库负载或适当增加任务超时时间。'
  }
  if (message.includes('password') || message.includes('authentication') || message.includes('ora-01017')) {
    return '数据库账号或密码不正确，请编辑数据源后重新测试连接。'
  }
  return '任务执行失败，请检查任务配置或展开技术详情获取更多信息。'
}

const load = async () => {
  loading.value = true
  try {
    const r = await request.get('/logs', {
      params: { page: page.value, page_size: pageSize.value, status: filter.value.status }
    })
    rows.value = r.list
    total.value = r.total
  } finally {
    loading.value = false
  }
}

const show = (row) => {
  current.value = row
  detail.value = true
}

onMounted(load)
</script>

<style scoped>
.hd {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pg {
  margin-top: 14px;
  justify-content: flex-end;
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0 18px;
  border-bottom: 1px solid #ebeef5;
}

.detail-head strong {
  display: block;
  margin-top: 6px;
  color: #253b46;
  font-size: 20px;
}

.detail-label {
  color: #909399;
  font-size: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 18px 0;
}

.detail-item {
  padding: 13px 14px;
  background: #f7f8fa;
  border-radius: 5px;
}

.detail-item span {
  display: block;
  color: #909399;
  font-size: 12px;
}

.detail-item strong {
  display: block;
  margin-top: 7px;
  color: #303133;
  font-size: 14px;
}

.error-panel {
  padding: 16px 18px;
  background: #fff5f5;
  border: 1px solid #fbc4c4;
  border-radius: 6px;
}

.error-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c45656;
}

.error-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
}

.friendly-error {
  margin: 12px 0 0;
  color: #5f2c2c;
  font-size: 14px;
  line-height: 1.7;
}

.technical-error {
  margin-top: 14px;
  color: #909399;
  font-size: 12px;
}

.technical-error summary {
  cursor: pointer;
  color: #909399;
}

.technical-error pre {
  max-height: 180px;
  margin: 10px 0 0;
  padding: 10px;
  overflow: auto;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

:deep(.el-result) {
  padding: 20px 0 8px;
}

@media (max-width: 680px) {
  .detail-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
