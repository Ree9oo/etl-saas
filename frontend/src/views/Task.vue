<template>
  <div class="page-card">
    <el-card>
      <template #header>
        <div class="hd">
          <span>同步任务</span>
          <el-button type="primary" :icon="Plus" @click="openCreate">新增任务</el-button>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="name" label="任务名称" min-width="140" />
        <el-table-column label="模式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.mode === 'full' ? 'primary' : 'warning'">
              {{ row.mode === 'full' ? '全量' : '增量' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="源表 → 目标表" min-width="200">
          <template #default="{ row }">{{ row.source_table }} → {{ row.target_table }}</template>
        </el-table-column>
        <el-table-column prop="cron" label="定时规则" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag[row.status]">{{ statusLabel[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="启用" width="90" class-name="enable-column">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="() => toggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" class-name="operation-column">
          <template #default="{ row }">
            <el-button size="small" type="success" :icon="VideoPlay" @click="run(row)" :loading="runningIds.has(row.id)" :disabled="row.status === 'running'">执行</el-button>
            <el-button size="small" type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog" :title="editing ? '编辑任务' : '新增任务'" width="600px">
      <el-form :model="form" label-width="88px" class="task-form">
        <div class="form-section-title">基础信息</div>
        <el-form-item label="任务名称" class="compact-item">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="源数据源" class="compact-item">
          <el-select v-model="form.source_id" style="width: 100%" placeholder="请选择源数据源" @change="onSourceChange">
            <el-option v-for="d in dsOptions" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标数据源" class="compact-item">
          <el-select v-model="form.target_id" style="width: 100%" placeholder="请选择目标数据源">
            <el-option v-for="d in dsOptions" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="源表" class="compact-item">
          <el-select v-model="form.source_table" filterable allow-create style="width: 100%"
                     :loading="tablesLoading" placeholder="选择或输入表名">
            <el-option v-for="t in tables" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标表" class="compact-item">
          <el-input v-model="form.target_table" placeholder="目标表名（不存在将自动创建）" />
        </el-form-item>
        <el-form-item label="同步模式" class="compact-item">
          <el-radio-group v-model="form.mode">
            <el-radio value="full">全量</el-radio>
            <el-radio value="incremental">增量</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="写入方式" v-if="form.mode === 'full'" class="compact-item">
          <el-radio-group v-model="form.write_mode">
            <el-radio value="truncate">清空后写入</el-radio>
            <el-radio value="append">追加写入</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="增量字段" v-if="form.mode === 'incremental'" class="compact-item">
          <el-input v-model="form.inc_field" placeholder="如 update_time" />
        </el-form-item>
        <el-collapse v-model="advancedOpen" class="advanced-settings">
          <el-collapse-item name="advanced">
            <template #title>
              <span>高级同步设置</span>
              <small>筛选、字段、批量和失败处理</small>
            </template>
            <el-form-item label="筛选条件" class="compact-item">
              <el-input v-model="form.where_condition" placeholder="可选，例如 status = 1" />
            </el-form-item>
            <el-form-item label="字段映射" class="compact-item">
              <el-input v-model="form.columns" placeholder="可选，留空同步全部字段" />
            </el-form-item>
            <el-form-item label="批量大小" class="compact-item">
              <el-input-number v-model="form.batch_size" :min="100" :max="50000" :step="500" />
            </el-form-item>
            <el-form-item label="失败重试" class="compact-item">
              <el-input-number v-model="form.retry_count" :min="0" :max="5" />
            </el-form-item>
            <el-form-item label="超时(秒)" class="compact-item">
              <el-input-number v-model="form.timeout" :min="60" :max="86400" :step="60" />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>

        <div class="schedule-section">
          <div class="schedule-heading">
            <div>
              <span class="form-section-title">定时调度</span>
              <small>不启用时可手动执行任务</small>
            </div>
            <el-switch v-model="form.enabled" active-text="已启用" inactive-text="未启用" />
          </div>
          <div class="cron-input">
            <el-input v-model="form.cron" placeholder="留空表示不定时，例如 0 2 * * *" />
            <el-button @click="openCronCalculator">计算公式</el-button>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="cronDialog" title="Cron 表达式计算" width="560px">
      <el-alert title="Cron 使用 5 段格式：分钟 小时 日 月 星期" type="info" :closable="false" />
      <el-form :model="cronForm" label-width="90px" class="cron-form">
        <el-form-item label="常用公式">
          <el-select v-model="cronPreset" style="width: 100%" @change="applyCronPreset">
            <el-option label="自定义" value="custom" />
            <el-option label="每分钟" value="every-minute" />
            <el-option label="每小时整点" value="hourly" />
            <el-option label="每天 02:00" value="daily" />
            <el-option label="每周一 02:00" value="weekly" />
            <el-option label="每月 1 日 02:00" value="monthly" />
          </el-select>
        </el-form-item>
        <el-form-item label="分钟">
          <el-input v-model="cronForm.minute" placeholder="0-59 或 *" @input="cronPreset = 'custom'" />
        </el-form-item>
        <el-form-item label="小时">
          <el-input v-model="cronForm.hour" placeholder="0-23 或 *" @input="cronPreset = 'custom'" />
        </el-form-item>
        <el-form-item label="日">
          <el-input v-model="cronForm.day" placeholder="1-31 或 *" @input="cronPreset = 'custom'" />
        </el-form-item>
        <el-form-item label="月">
          <el-input v-model="cronForm.month" placeholder="1-12 或 *" @input="cronPreset = 'custom'" />
        </el-form-item>
        <el-form-item label="星期">
          <el-input v-model="cronForm.week" placeholder="0-6（周日为 0）或 *" @input="cronPreset = 'custom'" />
        </el-form-item>
      </el-form>
      <div class="cron-preview">
        <span>生成结果</span>
        <code>{{ generatedCron }}</code>
      </div>
      <template #footer>
        <el-button @click="cronDialog = false">取消</el-button>
        <el-button type="primary" @click="useCron">使用此公式</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Edit, VideoPlay } from '@element-plus/icons-vue'
import request from '../utils/request'

const statusTag = { idle: 'info', running: 'warning', success: 'success', failed: 'danger' }
const statusLabel = { idle: '空闲', running: '运行中', success: '成功', failed: '失败' }

const list = ref([])
const dsOptions = ref([])
const tables = ref([])
const loading = ref(false)
const tablesLoading = ref(false)
const dialog = ref(false)
const saving = ref(false)
const editing = ref(false)
const runningIds = ref(new Set())
const cronDialog = ref(false)
const advancedOpen = ref([])
const cronPreset = ref('custom')
const cronForm = ref({ minute: '0', hour: '2', day: '*', month: '*', week: '*' })
const form = ref(emptyForm())

const generatedCron = computed(() => [
  cronForm.value.minute,
  cronForm.value.hour,
  cronForm.value.day,
  cronForm.value.month,
  cronForm.value.week
].join(' '))

function emptyForm() {
  return {
    id: null, name: '', source_id: null, target_id: null,
    source_table: '', target_table: '', mode: 'full', write_mode: 'truncate',
    inc_field: '', where_condition: '', columns: '', batch_size: 5000,
    cron: '', retry_count: 0, timeout: 3600, enabled: false
  }
}

const load = async () => {
  loading.value = true
  try {
    list.value = await request.get('/tasks')
  } finally {
    loading.value = false
  }
}

const loadDs = async () => {
  dsOptions.value = await request.get('/datasources')
}

const onSourceChange = async (id) => {
  if (!id) return
  tablesLoading.value = true
  try {
    tables.value = await request.get(`/datasources/${id}/tables`)
  } catch (e) {} finally {
    tablesLoading.value = false
  }
}

const openCreate = () => {
  form.value = emptyForm()
  editing.value = false
  advancedOpen.value = []
  dialog.value = true
}

const openEdit = (row) => {
  form.value = { ...row }
  editing.value = true
  advancedOpen.value = []
  dialog.value = true
  onSourceChange(row.source_id)
}

const applyCronPreset = (preset) => {
  const presets = {
    'every-minute': ['*', '*', '*', '*', '*'],
    hourly: ['0', '*', '*', '*', '*'],
    daily: ['0', '2', '*', '*', '*'],
    weekly: ['0', '2', '*', '*', '1'],
    monthly: ['0', '2', '1', '*', '*']
  }
  if (presets[preset]) {
    const [minute, hour, day, month, week] = presets[preset]
    cronForm.value = { minute, hour, day, month, week }
  }
}

const useCron = () => {
  form.value.cron = generatedCron.value
  cronDialog.value = false
}

const openCronCalculator = () => {
  const parts = (form.value.cron || '').trim().split(/\s+/)
  if (parts.length === 5) {
    const [minute, hour, day, month, week] = parts
    cronForm.value = { minute, hour, day, month, week }
  }
  cronPreset.value = 'custom'
  cronDialog.value = true
}

const save = async () => {
  saving.value = true
  try {
    if (editing.value) {
      const { id, ...body } = form.value
      await request.put(`/tasks/${id}`, body)
    } else {
      await request.post('/tasks', form.value)
    }
    ElMessage.success('保存成功')
    dialog.value = false
    load()
  } finally {
    saving.value = false
  }
}

const run = async (row) => {
  try {
    await ElMessageBox.confirm(`确认立即执行任务「${row.name}」？`, '执行任务', { type: 'warning' })
  } catch (e) {
    return
  }
  runningIds.value = new Set(runningIds.value).add(row.id)
  ElMessage.info(`任务「${row.name}」已开始执行，请稍候...`)
  try {
    const r = await request.post(`/tasks/${row.id}/run`)
    ElMessage.success(`同步成功，共 ${r.rows} 行（耗时 ${r.duration}s）`)
    load()
  } catch (e) {
    load()
  } finally {
    const ids = new Set(runningIds.value)
    ids.delete(row.id)
    runningIds.value = ids
  }
}

const toggle = async (row) => {
  try {
    await request.post(`/tasks/${row.id}/toggle`)
    ElMessage.success('状态已更新')
    load()
  } catch (e) {}
}

const remove = async (row) => {
  await ElMessageBox.confirm(`确认删除任务「${row.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/tasks/${row.id}`)
    ElMessage.success('已删除')
    load()
  } catch (e) {}
}

onMounted(async () => {
  await loadDs()
  load()
})
</script>

<style scoped>
.hd {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.enable-column) {
  border-right: 1px solid #dfe5eb !important;
}

:deep(.operation-column) {
  border-left: 1px solid #dfe5eb !important;
}

.task-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.form-section-title {
  display: block;
  margin: 2px 0 14px;
  color: #344d58;
  font-size: 14px;
  font-weight: 700;
}

.form-section-title::before {
  display: inline-block;
  width: 3px;
  height: 14px;
  margin-right: 8px;
  vertical-align: -2px;
  content: '';
  background: #409eff;
  border-radius: 2px;
}

.advanced-settings {
  margin: 4px 0 18px;
  border-top: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
}

.advanced-settings :deep(.el-collapse-item__header) {
  height: 48px;
  color: #52666f;
  font-size: 13px;
  font-weight: 600;
}

.advanced-settings :deep(.el-collapse-item__header small) {
  margin-left: 10px;
  color: #a0aab0;
  font-size: 12px;
  font-weight: 400;
}

.advanced-settings :deep(.el-collapse-item__wrap) {
  border-bottom: 0;
}

.schedule-section {
  padding: 14px 16px 16px;
  background: #f7fafc;
  border: 1px solid #e5edf3;
  border-radius: 6px;
}

.schedule-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.schedule-heading .form-section-title {
  display: inline-block;
  margin: 0;
}

.schedule-heading small {
  display: block;
  margin: 4px 0 0 11px;
  color: #95a1a8;
  font-size: 12px;
}

.cron-input {
  display: flex;
  width: 100%;
  gap: 8px;
}

.cron-input .el-input {
  flex: 1;
}

.schedule-section .cron-input :deep(.el-input__wrapper) {
  background: #fff;
}

.cron-form {
  margin-top: 18px;
}

.cron-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.cron-preview code {
  color: #409eff;
  font-weight: 600;
}
</style>
