<template>
  <div class="page-card dashboard-page">
    <div class="metric-grid">
      <div v-for="c in cards" :key="c.label" class="metric-card" :style="{ '--accent': c.color, '--tint': c.tint }">
        <div class="metric-icon"><el-icon :size="22"><component :is="c.icon" /></el-icon></div>
        <div class="metric-copy"><span>{{ c.label }}</span><strong>{{ c.value }}</strong></div>
        <span class="metric-mark">{{ c.mark }}</span>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="panel execution-panel">
        <div class="panel-heading">
          <div><span class="panel-kicker">EXECUTION HEALTH</span><h2>执行结果</h2></div>
          <span class="panel-note">累计 {{ stats.logs_total }} 次</span>
        </div>
        <div class="execution-content">
          <div class="donut" :style="{ '--success-rate': `${successRate}%` }"><div><strong>{{ successRate }}%</strong><span>成功率</span></div></div>
          <div class="legend-list">
            <div><i class="legend success"></i><span>执行成功</span><strong>{{ stats.logs_success }}</strong></div>
            <div><i class="legend failed"></i><span>执行失败</span><strong>{{ stats.logs_failed }}</strong></div>
            <div><i class="legend total"></i><span>总执行次数</span><strong>{{ stats.logs_total }}</strong></div>
          </div>
        </div>
      </section>

      <section class="panel task-panel">
        <div class="panel-heading">
          <div><span class="panel-kicker">TASK STATUS</span><h2>任务运行状态</h2></div>
          <el-button link type="primary" @click="router.push('/tasks')">管理任务 →</el-button>
        </div>
        <div class="bar-chart">
          <div class="bar-row"><span>已启用</span><div><i class="bar active" :style="{ width: taskRate }"></i></div><strong>{{ stats.tasks_enabled }}</strong></div>
          <div class="bar-row"><span>未启用</span><div><i class="bar idle" :style="{ width: idleTaskRate }"></i></div><strong>{{ idleTasks }}</strong></div>
          <div class="bar-row"><span>执行失败</span><div><i class="bar danger" :style="{ width: failedRate }"></i></div><strong>{{ stats.logs_failed }}</strong></div>
        </div>
        <div class="task-summary">共 {{ stats.tasks }} 个任务，{{ stats.tasks_enabled }} 个正在接受调度</div>
      </section>
    </div>

    <div class="bottom-grid">
      <section class="panel quick-panel">
        <div class="panel-heading"><div><span class="panel-kicker">QUICK ACCESS</span><h2>快捷入口</h2></div></div>
        <div class="quick-links"><button v-for="link in quickLinks" :key="link.label" type="button" @click="router.push(link.path)"><el-icon :color="link.color"><component :is="link.icon" /></el-icon><span>{{ link.label }}</span><b>→</b></button></div>
      </section>
      <section class="panel license-panel">
        <div class="panel-heading"><div><span class="panel-kicker">PLAN & USAGE</span><h2>授权与额度</h2></div><el-tag :type="planTag">{{ license.plan === 'paid' ? '付费版' : '免费版' }}</el-tag></div>
        <div class="usage-row"><span>数据源</span><div><i :style="{ width: usageWidth(license.datasources_used, license.max_datasources) }"></i></div><strong>{{ license.datasources_used }} / {{ fmt(license.max_datasources) }}</strong></div>
        <div class="usage-row"><span>同步任务</span><div><i class="orange" :style="{ width: usageWidth(license.tasks_used, license.max_tasks) }"></i></div><strong>{{ license.tasks_used }} / {{ fmt(license.max_tasks) }}</strong></div>
        <p class="license-state"><span :class="{ active: license.activated }"></span>{{ license.activated ? '授权已激活' : '当前为基础授权' }}</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'

const router = useRouter()
const stats = ref({ datasources: 0, tasks: 0, tasks_enabled: 0, logs_total: 0, logs_failed: 0, logs_success: 0 })
const license = ref({ plan: 'free', max_datasources: 3, max_tasks: 5, datasources_used: 0, tasks_used: 0, activated: false })

const planTag = computed(() => (license.value.plan === 'paid' ? 'success' : 'info'))
const fmt = (n) => (n === -1 ? '不限' : n)
const successRate = computed(() => stats.value.logs_total ? Math.round(stats.value.logs_success / stats.value.logs_total * 100) : 0)
const idleTasks = computed(() => Math.max(0, stats.value.tasks - stats.value.tasks_enabled))
const taskRate = computed(() => `${stats.value.tasks ? Math.max(8, stats.value.tasks_enabled / stats.value.tasks * 100) : 0}%`)
const idleTaskRate = computed(() => `${stats.value.tasks ? Math.max(8, idleTasks.value / stats.value.tasks * 100) : 0}%`)
const failedRate = computed(() => `${stats.value.logs_total ? Math.max(8, stats.value.logs_failed / stats.value.logs_total * 100) : 0}%`)
const usageWidth = (used, max) => max === -1 ? '35%' : `${Math.min(100, max ? used / max * 100 : 0)}%`

const cards = computed(() => [
  { label: '数据源', value: stats.value.datasources, mark: 'CONNECT', color: '#3d9b86', tint: '#e7f5f0', icon: 'Coin' },
  { label: '同步任务', value: stats.value.tasks, mark: 'TASKS', color: '#4b82df', tint: '#eaf0fc', icon: 'Sort' },
  { label: '启用任务', value: stats.value.tasks_enabled, mark: 'ACTIVE', color: '#e49a3a', tint: '#fff3df', icon: 'VideoPlay' },
  { label: '执行成功', value: stats.value.logs_success, mark: 'SUCCESS', color: '#758b8f', tint: '#edf1f1', icon: 'CircleCheck' }
])

const quickLinks = [
  { label: '数据源管理', path: '/datasources', color: '#3d9b86', icon: 'Coin' },
  { label: '同步任务', path: '/tasks', color: '#4b82df', icon: 'Sort' },
  { label: '执行日志', path: '/logs', color: '#e49a3a', icon: 'Document' }
]

onMounted(async () => {
  stats.value = await request.get('/stats')
  license.value = await request.get('/license/info')
})
</script>

<style scoped>
.dashboard-page { background: #f3f5f6; }
.welcome-line, .panel-heading, .execution-content, .schedule-heading { display: flex; align-items: center; justify-content: space-between; }
.welcome-line { margin-bottom: 22px; }
.eyebrow, .panel-kicker { margin: 0; color: #8a989a; font-size: 10px; font-weight: 700; letter-spacing: .16em; }
.welcome-line h1 { margin: 6px 0 4px; color: #233b45; font-size: 25px; }
.welcome-line p:last-child { margin: 0; color: #8b969a; font-size: 13px; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.metric-card { position: relative; display: flex; align-items: center; min-height: 112px; padding: 20px; overflow: hidden; background: #fff; border: 1px solid #e5eaed; border-radius: 6px; box-shadow: 0 5px 16px rgba(37, 59, 69, .04); }
.metric-card::after { position: absolute; right: -22px; bottom: -30px; width: 90px; height: 90px; content: ''; border: 1px solid var(--accent); border-radius: 50%; opacity: .12; }
.metric-icon { display: grid; width: 44px; height: 44px; margin-right: 14px; place-items: center; color: var(--accent); background: var(--tint); border-radius: 10px; }
.metric-copy span { display: block; color: #8c999d; font-size: 12px; }
.metric-copy strong { display: block; margin-top: 4px; color: #263c45; font-size: 28px; line-height: 1; }
.metric-mark { position: absolute; right: 16px; top: 19px; color: var(--accent); font-size: 9px; letter-spacing: .12em; opacity: .65; }
.dashboard-grid, .bottom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
.panel { padding: 20px; background: #fff; border: 1px solid #e5eaed; border-radius: 6px; box-shadow: 0 5px 16px rgba(37, 59, 69, .04); }
.panel-heading { align-items: flex-start; margin-bottom: 20px; }
.panel-heading h2 { margin: 6px 0 0; color: #2c4650; font-size: 17px; }
.panel-note, .task-summary { color: #9aa5a8; font-size: 12px; }
.execution-content { justify-content: flex-start; gap: 38px; min-height: 150px; }
.donut { position: relative; display: grid; width: 142px; height: 142px; place-items: center; border-radius: 50%; background: conic-gradient(#3d9b86 var(--success-rate), #edf1f1 0); }
.donut::before { position: absolute; width: 104px; height: 104px; content: ''; background: #fff; border-radius: 50%; }
.donut > div { position: relative; z-index: 1; text-align: center; }
.donut strong { display: block; color: #29474e; font-size: 25px; }
.donut span { color: #9aa5a8; font-size: 11px; }
.legend-list { flex: 1; }
.legend-list div { display: flex; align-items: center; margin: 15px 0; color: #718186; font-size: 13px; }
.legend-list strong { margin-left: auto; color: #304952; }
.legend { width: 8px; height: 8px; margin-right: 9px; border-radius: 50%; }
.legend.success { background: #3d9b86; }.legend.failed { background: #e97970; }.legend.total { background: #b4c2c4; }
.bar-chart { padding: 7px 0 4px; }
.bar-row { display: grid; grid-template-columns: 65px 1fr 30px; align-items: center; gap: 12px; margin: 18px 0; color: #718186; font-size: 12px; }
.bar-row > div, .usage-row > div { height: 8px; overflow: hidden; background: #edf1f2; border-radius: 8px; }
.bar { display: block; height: 100%; min-width: 8px; border-radius: 8px; }.bar.active { background: #4b82df; }.bar.idle { background: #b4c2c4; }.bar.danger { background: #e97970; }
.bar-row strong { color: #304952; text-align: right; }
.task-summary { margin-top: 22px; padding-top: 15px; border-top: 1px solid #eef1f2; }
.quick-links { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.quick-links button { display: flex; align-items: center; gap: 10px; padding: 14px 12px; color: #52676e; text-align: left; cursor: pointer; background: #f7f9fa; border: 1px solid #e7edef; border-radius: 5px; }
.quick-links button:hover { border-color: #9bcfc1; background: #f1faf7; }.quick-links span { flex: 1; font-size: 13px; }.quick-links b { color: #a0afb1; font-size: 16px; }
.usage-row { display: grid; grid-template-columns: 58px 1fr 82px; align-items: center; gap: 12px; margin: 20px 0; color: #718186; font-size: 12px; }.usage-row i { display: block; height: 100%; background: #3d9b86; border-radius: 8px; }.usage-row i.orange { background: #e49a3a; }.usage-row strong { color: #425c63; font-size: 12px; text-align: right; }
.license-state { margin: 22px 0 0; color: #92a0a3; font-size: 12px; }.license-state span { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #b7c1c3; }.license-state span.active { background: #3d9b86; box-shadow: 0 0 0 4px #e4f4ef; }
@media (max-width: 900px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 650px) { .welcome-line { align-items: flex-start; gap: 14px; flex-direction: column; }.dashboard-grid, .bottom-grid { grid-template-columns: 1fr; }.metric-grid { grid-template-columns: 1fr 1fr; gap: 10px; }.metric-card { padding: 14px; }.metric-mark { display: none; }.execution-content { gap: 20px; }.donut { width: 120px; height: 120px; }.donut::before { width: 88px; height: 88px; } }
</style>
