<template>
  <div class="page-card">
    <section class="recent-section">
      <div class="section-heading">
        <div>
          <span class="section-kicker">CONNECTORS</span>
          <h2>最近使用的数据库</h2>
        </div>
        <span class="section-note">选择类型，快速创建数据源</span>
      </div>
      <div class="type-grid">
        <button
          v-for="item in recentTypes"
          :key="item.key"
          class="type-card"
          :style="{ '--brand': item.color, '--brand-soft': item.soft }"
          type="button"
          @click="openCreate(item.key)"
        >
          <span class="type-logo">
            <img :src="item.icon" :alt="`${item.label} 图标`" @error="$event.target.style.display = 'none'" />
          </span>
          <span class="type-name">{{ item.label }}</span>
          <span class="type-action">新建连接 <span>→</span></span>
        </button>
      </div>
    </section>

    <el-card>
      <template #header>
        <div class="hd">
          <span>数据源列表</span>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="db_type" label="类型" width="160">
          <template #default="{ row }">
            <span class="db-type-cell">
              <img
                v-if="typeVisual[row.db_type]?.icon"
                :src="typeVisual[row.db_type].icon"
                :alt="`${typeLabel[row.db_type] || row.db_type} 图标`"
                :style="{ background: typeVisual[row.db_type]?.color || '#7b8794' }"
              />
              <span>{{ typeLabel[row.db_type] || row.db_type }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="地址" min-width="160">
          <template #default="{ row }">{{ row.host || '-' }}:{{ row.port }}</template>
        </el-table-column>
        <el-table-column prop="database" label="数据库" />
        <el-table-column prop="username" label="用户名" min-width="140" class-name="username-column" />
        <el-table-column label="操作" width="300" fixed="right" class-name="operation-column">
          <template #default="{ row }">
            <el-button size="small" :icon="Connection" @click="test(row)">连通测试</el-button>
            <el-button size="small" type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog" :title="editing ? '编辑数据源' : '新增数据源'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="数据源名称" />
        </el-form-item>
        <el-form-item label="数据库类型">
          <el-select v-model="form.db_type" style="width: 100%" @change="onTypeChange">
            <el-option v-for="(v, k) in typeLabel" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
        <div class="type-hint">
          <span class="type-hint__mark" :style="{ background: typeVisual[form.db_type]?.color }">
            <img :src="typeVisual[form.db_type]?.icon" :alt="`${currentType.label} 图标`" />
          </span>
          <div>
            <strong>{{ currentType.label }}连接配置</strong>
            <p>{{ currentType.description }}</p>
          </div>
        </div>
        <el-form-item v-if="currentType.showHost" label="主机地址">
          <el-input v-model="form.host" :placeholder="currentType.hostPlaceholder" />
        </el-form-item>
        <el-form-item v-if="currentType.showPort" label="端口">
          <el-input-number v-model="form.port" :min="1" :max="65535" controls-position="right" />
        </el-form-item>
        <el-form-item v-if="currentType.showAuth" label="用户名">
          <el-input v-model="form.username" :placeholder="currentType.usernamePlaceholder" />
        </el-form-item>
        <el-form-item v-if="currentType.showAuth" label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :disabled="editing"
            :placeholder="editing ? '已保存，不显示密码' : '请输入连接密码'"
          />
        </el-form-item>
        <el-form-item :label="currentType.databaseLabel">
          <el-input v-model="form.database" :placeholder="currentType.databasePlaceholder" />
        </el-form-item>
        <el-form-item v-if="currentType.showCharset" label="字符集">
          <el-select v-model="form.charset" style="width: 100%">
            <el-option label="UTF-8 / utf8mb4" value="utf8mb4" />
            <el-option label="UTF-8 / utf8" value="utf8" />
            <el-option label="Latin-1 / latin1" value="latin1" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button :loading="testing" @click="testForm">连通测试</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Connection, Edit } from '@element-plus/icons-vue'
import request from '../utils/request'

const typeLabel = {
  mysql: 'MySQL',
  sqlserver: 'SQLServer',
  postgresql: 'PostgreSQL',
  oracle: 'Oracle',
  dm: '达梦',
  sqlite: 'SQLite'
}
const typeConfig = {
  mysql: {
    short: 'MY', label: 'MySQL', defaultPort: 3306, showHost: true, showPort: true,
    showAuth: true, showCharset: true, hostPlaceholder: '如 127.0.0.1',
    usernamePlaceholder: '如 root', databaseLabel: '数据库名', databasePlaceholder: '请输入数据库名',
    description: '适用于 MySQL 5.7+ / 8.0，支持字符集选择。'
  },
  sqlserver: {
    short: 'MS', label: 'SQL Server', defaultPort: 1433, showHost: true, showPort: true,
    showAuth: true, showCharset: false, hostPlaceholder: '如 127.0.0.1',
    usernamePlaceholder: 'SQL Server 登录名', databaseLabel: '数据库名', databasePlaceholder: '如 master',
    description: '使用 SQL Server 专用驱动建立安全连接。'
  },
  postgresql: {
    short: 'PG', label: 'PostgreSQL', defaultPort: 5432, showHost: true, showPort: true,
    showAuth: true, showCharset: false, hostPlaceholder: '如 127.0.0.1',
    usernamePlaceholder: '如 postgres', databaseLabel: '数据库名', databasePlaceholder: '如 postgres',
    description: '适用于 PostgreSQL 12+，默认使用标准数据库连接。'
  },
  oracle: {
    short: 'OR', label: 'Oracle', defaultPort: 1521, showHost: true, showPort: true,
    showAuth: true, showCharset: false, hostPlaceholder: 'Oracle 服务器地址',
    usernamePlaceholder: 'Oracle 用户名', databaseLabel: 'Service Name', databasePlaceholder: '如 ORCL 或 XEPDB1',
    description: '填写 Oracle Service Name，而不是本地连接别名。'
  },
  dm: {
    short: 'DM', label: '达梦', defaultPort: 5236, showHost: true, showPort: true,
    showAuth: true, showCharset: false, hostPlaceholder: '达梦服务器地址',
    usernamePlaceholder: '如 SYSDBA', databaseLabel: '数据库名', databasePlaceholder: '请输入数据库名',
    description: '使用达梦专用连接协议，默认端口为 5236。'
  },
  sqlite: {
    short: 'SQ', label: 'SQLite', defaultPort: 0, showHost: false, showPort: false,
    showAuth: false, showCharset: false, hostPlaceholder: '',
    usernamePlaceholder: '', databaseLabel: '文件路径', databasePlaceholder: '如 ./data/app.db 或绝对路径',
    description: '无需服务器、端口或账号，填写本地 SQLite 文件路径即可。'
  }
}
const typeVisual = {
  mysql: { color: '#32c94a', soft: '#e7f6e9', icon: 'https://cdn.simpleicons.org/mysql/ffffff' },
  oracle: { color: '#f9003d', soft: '#ffeaed', icon: '/database-icons/oracle.svg' },
  postgresql: { color: '#4385f5', soft: '#e9efff', icon: 'https://cdn.simpleicons.org/postgresql/ffffff' },
  sqlserver: { color: '#ffab00', soft: '#fff5dc', icon: 'https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/microsoftsqlserver/microsoftsqlserver-original.svg' },
  dm: { color: '#e17c53', soft: '#fff0e9', icon: '/database-icons/dameng.svg' },
  sqlite: { color: '#5accc7', soft: '#e5f8f7', icon: 'https://cdn.simpleicons.org/sqlite/ffffff' }
}
const quickTypeOrder = ['mysql', 'oracle', 'postgresql', 'sqlserver', 'dm', 'sqlite']
const list = ref([])
const loading = ref(false)
const dialog = ref(false)
const saving = ref(false)
const testing = ref(false)
const editing = ref(false)
const form = ref(emptyForm())
const testResult = ref(null)
const currentType = computed(() => typeConfig[form.value.db_type] || typeConfig.mysql)
const recentTypes = computed(() => {
  const used = list.value.map((item) => item.db_type).filter((type, index, items) => (
    typeConfig[type] && items.indexOf(type) === index
  ))
  const keys = [...used, ...quickTypeOrder.filter((type) => !used.includes(type))]
  return keys.slice(0, 6).map((key) => ({
    key,
    label: typeLabel[key],
    short: typeConfig[key].short,
    ...typeVisual[key]
  }))
})

function emptyForm() {
  return {
    name: '', db_type: 'mysql', host: '', port: 3306,
    username: '', password: '', database: '', charset: 'utf8mb4'
  }
}

const load = async () => {
  loading.value = true
  try {
    list.value = await request.get('/datasources')
  } finally {
    loading.value = false
  }
}

const openCreate = (type = 'mysql') => {
  form.value = emptyForm()
  editing.value = false
  form.value.db_type = type
  onTypeChange(type)
  dialog.value = true
}

const openEdit = (row) => {
  editing.value = true
  form.value = {
    id: row.id,
    name: row.name,
    db_type: row.db_type,
    host: row.host || '',
    port: row.port,
    username: row.username || '',
    password: '',
    database: row.database || '',
    charset: row.charset || ''
  }
  dialog.value = true
}

const onTypeChange = (type) => {
  const config = typeConfig[type]
  form.value.port = config.defaultPort
  form.value.charset = type === 'mysql' ? 'utf8mb4' : ''
  if (type === 'sqlite') {
    form.value.host = ''
    form.value.username = ''
    form.value.password = ''
  }
}

const testForm = async () => {
  testing.value = true
  try {
    const r = editing.value
      ? await request.post(`/datasources/${form.value.id}/test`)
      : await request.post('/datasources/test', form.value)
    ElMessage.success(r.message || '连接成功')
  } catch (e) {}
  finally {
    testing.value = false
  }
}

const test = async (row) => {
  try {
    await request.post(`/datasources/${row.id}/test`)
    ElMessage.success('连接成功')
  } catch (e) {}
}

const save = async () => {
  saving.value = true
  try {
    if (editing.value) {
      const { id, ...body } = form.value
      await request.put(`/datasources/${id}`, body)
    } else {
      await request.post('/datasources', form.value)
    }
    ElMessage.success(editing.value ? '更新成功' : '新增成功')
    dialog.value = false
    load()
  } finally {
    saving.value = false
  }
}

const remove = async (row) => {
  await ElMessageBox.confirm(`确认删除数据源「${row.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/datasources/${row.id}`)
    ElMessage.success('已删除')
    load()
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.recent-section {
  margin-bottom: 18px;
  padding: 20px 22px 22px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-kicker {
  color: #8b969f;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.section-heading h2 {
  margin: 5px 0 0;
  color: #253b46;
  font-size: 18px;
  font-weight: 700;
}

.section-note {
  color: #a1a9af;
  font-size: 12px;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(100px, 1fr));
  gap: 12px;
}

.type-card {
  position: relative;
  min-height: 142px;
  padding: 14px 10px 12px;
  overflow: hidden;
  color: #283d47;
  text-align: center;
  cursor: pointer;
  background: #fff;
  border: 1px solid #e4e9ed;
  border-radius: 5px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.type-card::after {
  position: absolute;
  right: -16px;
  bottom: -22px;
  width: 66px;
  height: 66px;
  content: '';
  border: 1px solid var(--brand);
  border-radius: 50%;
  opacity: 0.12;
}

.type-card:hover {
  border-color: var(--brand);
  box-shadow: 0 8px 20px rgba(38, 58, 70, 0.1);
  transform: translateY(-2px);
}

.type-logo {
  position: relative;
  display: grid;
  width: 56px;
  height: 56px;
  margin: 0 auto 10px;
  place-items: center;
  color: #fff;
  background: var(--brand);
  border-radius: 9px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.02em;
  box-shadow: 0 5px 10px color-mix(in srgb, var(--brand) 25%, transparent);
}

.type-logo img {
  position: absolute;
  width: 38px;
  height: 38px;
  object-fit: contain;
}

.type-name {
  display: block;
  font-size: 14px;
  font-weight: 600;
}

.type-action {
  display: block;
  margin-top: 8px;
  color: var(--brand);
  font-size: 10px;
  opacity: 0;
  transform: translateY(3px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.type-card:hover .type-action {
  opacity: 1;
  transform: translateY(0);
}

.type-action span { font-size: 13px; }

.db-type-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #49616d;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.db-type-cell img {
  flex: 0 0 30px;
  width: 30px;
  height: 30px;
  padding: 3px;
  object-fit: contain;
  border-radius: 5px;
}

.hd {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-table__body-wrapper td),
:deep(.el-table__header-wrapper th) {
  border-right: 1px solid #ebeef5;
}

:deep(.el-table__body-wrapper td:last-child),
:deep(.el-table__header-wrapper th:last-child) {
  border-right: 0;
}

.type-hint {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 2px 0 20px 90px;
  padding: 12px 14px;
  color: #4c6470;
  background: #f4f8f7;
  border: 1px solid #dcece7;
  border-radius: 6px;
}

.type-hint__mark {
  display: grid;
  flex: 0 0 34px;
  height: 34px;
  place-items: center;
  color: #176b5a;
  background: #d6f0e8;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.type-hint__mark img {
  width: 25px;
  height: 25px;
  object-fit: contain;
}

:deep(.username-column) {
  border-right: 1px solid #dfe5eb !important;
}

:deep(.operation-column) {
  border-left: 1px solid #dfe5eb !important;
}

.type-hint strong {
  display: block;
  color: #31535c;
  font-size: 13px;
}

.type-hint p {
  margin: 4px 0 0;
  color: #819293;
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 1050px) {
  .type-grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
}

@media (max-width: 600px) {
  .recent-section { padding: 16px; }
  .section-note { display: none; }
  .type-grid { grid-template-columns: repeat(2, minmax(110px, 1fr)); }
}
</style>
