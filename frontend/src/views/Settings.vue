<template>
  <div class="page-card">
    <el-card style="margin-bottom: 16px">
      <template #header>告警配置（任务失败推送）</template>
      <el-form :model="alert" label-width="140px" style="max-width: 560px">
        <el-form-item label="钉钉 Webhook">
          <el-input v-model="alert.dingtalk_webhook" placeholder="钉钉机器人 Webhook 地址" />
        </el-form-item>
        <el-form-item label="企业微信 Webhook">
          <el-input v-model="alert.wechat_webhook" placeholder="企业微信机器人 Webhook 地址" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveAlert">保存配置</el-button>
        </el-form-item>
        <div class="hint">未配置 Webhook 时不推送，不影响同步任务执行。</div>
      </el-form>
    </el-card>

    <el-card>
      <template #header>授权与额度</template>
      <el-descriptions :column="2" border style="margin-bottom: 16px">
        <el-descriptions-item label="当前版本">
          <el-tag :type="lic.plan === 'paid' ? 'success' : 'info'">
            {{ lic.plan === 'paid' ? '付费版' : '免费版' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据源额度">
          {{ fmt(lic.max_datasources) }}（已用 {{ lic.datasources_used }}）
        </el-descriptions-item>
        <el-descriptions-item label="任务额度">
          {{ fmt(lic.max_tasks) }}（已用 {{ lic.tasks_used }}）
        </el-descriptions-item>
        <el-descriptions-item label="授权状态">
          {{ lic.activated ? '已激活' : '未激活' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-form :model="activate" label-width="140px" style="max-width: 560px">
        <el-form-item label="授权码">
          <el-input v-model="activate.license_code" placeholder="私有化部署授权码（以 ETL- 开头）" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" :loading="activating" @click="doActivate">激活授权</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="hd">
          <span>操作日志</span>
          <el-button :icon="Refresh" @click="loadActions">刷新</el-button>
        </div>
      </template>
      <el-table :data="actionRows" v-loading="actionLoading" border stripe>
        <el-table-column prop="username" label="操作人" width="140" />
        <el-table-column prop="module" label="模块" width="140" />
        <el-table-column prop="action" label="操作" width="180" />
        <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP属地" width="150" />
        <el-table-column label="操作时间" width="180">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-pagination
        class="pg"
        v-model:current-page="actionPage"
        :page-size="actionPageSize"
        :total="actionTotal"
        @current-change="loadActions"
        layout="total, prev, pager, next"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const alert = ref({ dingtalk_webhook: '', wechat_webhook: '' })
const lic = ref({ plan: 'free', max_datasources: 3, max_tasks: 5, datasources_used: 0, tasks_used: 0, activated: false })
const activate = ref({ license_code: '' })
const saving = ref(false)
const activating = ref(false)
const actionRows = ref([])
const actionTotal = ref(0)
const actionPage = ref(1)
const actionPageSize = 20
const actionLoading = ref(false)
const fmt = (n) => (n === -1 ? '不限' : n)
const fmtTime = (t) => (t ? t.replace('T', ' ').slice(0, 19) : '-')

const load = async () => {
  alert.value = await request.get('/system/alert')
  lic.value = await request.get('/license/info')
}
const saveAlert = async () => {
  saving.value = true
  try {
    await request.put('/system/alert', alert.value)
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}
const doActivate = async () => {
  activating.value = true
  try {
    const r = await request.post('/license/activate', activate.value)
    ElMessage.success(r.msg || '激活成功')
    load()
  } catch (e) {} finally {
    activating.value = false
  }
}

const loadActions = async () => {
  actionLoading.value = true
  try {
    const result = await request.get('/system/action-logs', {
      params: { page: actionPage.value, page_size: actionPageSize }
    })
    actionRows.value = result.list
    actionTotal.value = result.total
  } finally {
    actionLoading.value = false
  }
}

onMounted(() => {
  load()
  loadActions()
})
</script>

<style scoped>
.hint {
  color: #909399;
  font-size: 12px;
}
.hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.pg {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
