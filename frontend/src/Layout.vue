<template>
  <el-container class="fill">
    <el-aside width="220px" style="background: #001529">
      <div class="logo">
        <el-icon><Switch /></el-icon>
        <span>ETL 数据同步</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#001529"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon><span>概览</span>
        </el-menu-item>
        <el-menu-item index="/datasources">
          <el-icon><Coin /></el-icon><span>数据源管理</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><Sort /></el-icon><span>同步任务</span>
        </el-menu-item>
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon><span>执行日志</span>
        </el-menu-item>
        <el-menu-item v-if="user.role === 'admin'" index="/settings">
          <el-icon><Setting /></el-icon><span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header
        style="
          background: #fff;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid #eee;
        "
      >
        <span style="font-weight: 600">{{ title }}</span>
        <el-dropdown @command="onCommand">
          <span class="user">
            <el-icon><User /></el-icon> {{ user.username || '用户' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main style="padding: 0">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const user = JSON.parse(localStorage.getItem('user') || '{}')

const titles = {
  dashboard: '概览',
  datasources: '数据源管理',
  tasks: '同步任务',
  logs: '执行日志',
  settings: '系统设置'
}
const title = computed(() => titles[route.name] || 'ETL 数据同步')
const activeMenu = computed(() => '/' + (route.path.split('/')[1] || 'dashboard'))

const onCommand = (cmd) => {
  if (cmd === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
}
</script>

<style scoped>
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  padding: 0 18px;
}
.user {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
