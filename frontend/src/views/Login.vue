<template>
  <div class="login-wrap">
    <section class="visual-panel" aria-label="ETL 数据流概览">
      <div class="visual-noise"></div>
      <div class="visual-topline">
        <div class="brand-mark"><el-icon><Switch /></el-icon></div>
        <span>ETL / CONTROL ROOM</span>
      </div>
      <div class="visual-copy">
        <p class="eyebrow">MAKE DATA MOVE</p>
        <h1>把分散的数据，<br /><em>流向正确的地方。</em></h1>
        <p class="intro">连接、清洗、同步，一处掌控多源数据流转。</p>
      </div>
      <div class="pipeline" aria-hidden="true">
        <div class="pipeline-label source-label">SOURCE</div>
        <div class="pipeline-label target-label">TARGET</div>
        <div class="node node-source"><span></span><b>MYSQL</b></div>
        <div class="node node-transform"><span></span><b>ETL</b></div>
        <div class="node node-target"><span></span><b>WAREHOUSE</b></div>
        <div class="route route-one"><i></i></div>
        <div class="route route-two"><i></i></div>
      </div>
      <div class="visual-footer">
        <span><i class="status-dot"></i> SYSTEM READY</span>
        <span>v1.0 / DATA SYNC</span>
      </div>
    </section>

    <section class="form-panel">
      <div class="form-inner">
        <div class="mobile-mark"><el-icon><Switch /></el-icon></div>
        <p class="form-kicker">{{ isRegister ? '创建工作空间' : '欢迎回来' }}</p>
        <h2>{{ isRegister ? '注册 ETL SaaS' : '登录 ETL SaaS' }}</h2>
        <p class="form-desc">{{ isRegister ? '注册账号，开始管理你的数据同步任务' : '进入你的数据同步控制台' }}</p>
        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent>
          <el-form-item prop="username">
            <label for="username">用户名</label>
            <el-input id="username" v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <label for="password">密码</label>
            <el-input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="onLogin"
            />
          </el-form-item>
          <el-form-item v-if="isRegister" prop="confirmPassword">
            <label for="confirm-password">确认密码</label>
            <el-input
              id="confirm-password"
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="onLogin"
            />
          </el-form-item>
          <el-button type="primary" :loading="loading" class="btn" @click="onLogin">
            {{ isRegister ? '创建账号' : '进入控制台' }} <span class="button-arrow">→</span>
          </el-button>
        </el-form>
        <div class="tip">
          <template v-if="!isRegister">
            <span>演示账号</span>
            <b>free / 123456</b>
          </template>
          <template v-else>
            <span>已有账号？</span>
            <a href="/login" @click.prevent="router.push('/login')">返回登录</a>
          </template>
        </div>
        <div v-if="!isRegister" class="auth-switch">
          <span>还没有账号？</span>
          <a href="/register" @click.prevent="router.push('/register')">立即注册</a>
        </div>
        <div class="form-footer">SECURE DATA OPERATIONS <span>·</span> ETL SAAS</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Switch } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const route = useRoute()
const isRegister = computed(() => route.path === '/register')
const form = ref({ username: isRegister.value ? '' : '', password: isRegister.value ? '' : '', confirmPassword: '' })
const loading = ref(false)
const formRef = ref()

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 64, message: '用户名长度为 3-64 位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度为 6-128 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        callback(value === form.value.password ? undefined : new Error('两次输入的密码不一致'))
      },
      trigger: 'blur'
    }
  ]
}

watch(
  () => route.path,
  () => {
    form.value = {
      username: route.path === '/register' ? '' : '',
      password: route.path === '/register' ? '' : '',
      confirmPassword: ''
    }
    formRef.value?.clearValidate()
  }
)

const onLogin = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const endpoint = isRegister.value ? '/auth/register' : '/auth/login'
      const data = await request.post(endpoint, {
        username: form.value.username,
        password: form.value.password
      })
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data))
      ElMessage.success(isRegister.value ? '注册成功，已自动登录' : '登录成功')
      router.push('/dashboard')
    } catch (e) {
      // 错误已由拦截器提示
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-wrap {
  min-height: 100%;
  display: flex;
  overflow: hidden;
  background: #f4f0e8;
}
.visual-panel {
  position: relative;
  width: 56%;
  min-height: 100vh;
  overflow: hidden;
  padding: 42px 5vw 34px;
  color: #edf7f4;
  background: #102d3d;
  isolation: isolate;
}
.visual-panel::before,
.visual-panel::after {
  content: '';
  position: absolute;
  z-index: -1;
  border: 1px solid rgba(114, 215, 193, 0.16);
  border-radius: 50%;
}
.visual-panel::before {
  width: 56vw;
  height: 56vw;
  right: -30vw;
  top: -20vw;
}
.visual-panel::after {
  width: 42vw;
  height: 42vw;
  left: -27vw;
  bottom: -21vw;
}
.visual-noise {
  position: absolute;
  inset: 0;
  z-index: -1;
  opacity: 0.22;
  background-image: linear-gradient(rgba(144, 218, 201, 0.09) 1px, transparent 1px),
    linear-gradient(90deg, rgba(144, 218, 201, 0.09) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(to bottom, black, transparent 80%);
}
.visual-topline,
.visual-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #8ab7b5;
  font-size: 10px;
  letter-spacing: 0.14em;
}
.brand-mark,
.mobile-mark {
  display: grid;
  place-items: center;
  color: #102d3d;
  background: #8bd8c1;
  border-radius: 8px;
}
.brand-mark {
  width: 30px;
  height: 30px;
  font-size: 18px;
}
.visual-copy {
  position: relative;
  z-index: 1;
  max-width: 550px;
  margin-top: 18vh;
}
.eyebrow,
.form-kicker {
  margin: 0 0 18px;
  color: #8bd8c1;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.2em;
}
.visual-copy h1 {
  margin: 0;
  color: #f4fbf7;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(38px, 4.1vw, 66px);
  font-weight: 400;
  line-height: 1.08;
  letter-spacing: -0.02em;
}
.visual-copy h1 em {
  color: #8bd8c1;
  font-style: normal;
}
.intro {
  margin: 25px 0 0;
  color: #a6c5c3;
  font-size: 15px;
  letter-spacing: 0.04em;
}
.pipeline {
  position: absolute;
  right: 10%;
  bottom: 20%;
  width: 72%;
  height: 152px;
  opacity: 0.9;
}
.node {
  position: absolute;
  top: 52px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #d8ece7;
  font-size: 10px;
  letter-spacing: 0.11em;
}
.node span {
  display: block;
  width: 12px;
  height: 12px;
  border: 3px solid #8bd8c1;
  border-radius: 50%;
  background: #102d3d;
  box-shadow: 0 0 0 6px rgba(139, 216, 193, 0.09), 0 0 18px rgba(139, 216, 193, 0.55);
}
.node-source { left: 0; }
.node-transform { left: 43%; color: #8bd8c1; }
.node-target { right: 0; }
.route {
  position: absolute;
  top: 58px;
  height: 1px;
  background: rgba(139, 216, 193, 0.38);
}
.route-one { left: 12%; width: 30%; }
.route-two { left: 55%; width: 30%; }
.route i {
  position: absolute;
  top: -3px;
  left: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f2b07b;
  box-shadow: 0 0 12px #f2b07b;
  animation: flow 3s linear infinite;
}
.route-two i { animation-delay: 1.5s; }
.pipeline-label {
  position: absolute;
  top: 24px;
  color: #668f91;
  font-size: 9px;
  letter-spacing: 0.16em;
}
.source-label { left: 0; }
.target-label { right: 0; }
.visual-footer {
  position: absolute;
  right: 5vw;
  bottom: 34px;
  left: 5vw;
}
.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 7px;
  border-radius: 50%;
  background: #8bd8c1;
  box-shadow: 0 0 10px #8bd8c1;
}
.form-panel {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  min-width: 440px;
  padding: 48px 7vw;
  background: #f4f0e8;
}
.form-inner { width: min(100%, 390px); }
.mobile-mark { display: none; }
.form-kicker { margin-bottom: 12px; color: #d17a50; }
.form-inner h2 {
  margin: 0;
  color: #183743;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.form-desc {
  margin: 10px 0 38px;
  color: #7d8988;
  font-size: 14px;
}
.form-inner :deep(.el-form-item) { margin-bottom: 22px; }
.form-inner label {
  display: block;
  margin-bottom: 8px;
  color: #3b555b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.form-inner :deep(.el-input__wrapper) {
  min-height: 48px;
  padding: 1px 14px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid #d8d7d0;
  border-radius: 6px;
  box-shadow: none;
}
.form-inner :deep(.el-input__wrapper.is-focus) {
  border-color: #5aa997;
  box-shadow: 0 0 0 3px rgba(90, 169, 151, 0.14);
}
.form-inner :deep(.el-input__inner) { color: #183743; }
.btn {
  width: 100%;
  height: 48px;
  margin-top: 5px;
  border: 0;
  border-radius: 6px;
  color: #102d3d;
  font-weight: 700;
  background: #8bd8c1;
  box-shadow: 0 8px 18px rgba(61, 139, 119, 0.18);
}
.btn:hover,
.btn:focus { color: #102d3d; background: #a2e3d0; }
.button-arrow { margin-left: 8px; font-size: 18px; line-height: 0; }
.tip {
  display: flex;
  justify-content: space-between;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid #dedbd3;
  color: #969d99;
  font-size: 12px;
}
.tip b { color: #5d7776; font-weight: 600; }
.tip a {
  color: #3d9b86;
  font-weight: 600;
  text-decoration: none;
}
.tip a:hover { color: #287761; }
.auth-switch {
  margin-top: 16px;
  color: #969d99;
  font-size: 12px;
  text-align: center;
}
.auth-switch a {
  margin-left: 5px;
  color: #3d9b86;
  font-weight: 600;
  text-decoration: none;
}
.auth-switch a:hover { color: #287761; }
.form-footer {
  margin-top: 72px;
  color: #b5b2a9;
  font-size: 9px;
  letter-spacing: 0.16em;
  text-align: center;
}
.form-footer span { margin: 0 8px; }
@keyframes flow {
  from { transform: translateX(0); opacity: 0; }
  15% { opacity: 1; }
  85% { opacity: 1; }
  to { transform: translateX(30vw); opacity: 0; }
}
@media (max-width: 820px) {
  .visual-panel { display: none; }
  .form-panel {
    min-width: 0;
    min-height: 100vh;
    padding: 38px 26px;
  }
  .mobile-mark {
    display: grid;
    width: 38px;
    height: 38px;
    margin-bottom: 44px;
    font-size: 20px;
  }
  .form-footer { margin-top: 54px; }
}
@media (min-width: 821px) and (max-width: 1100px) {
  .form-panel { padding: 48px 5vw; }
}
</style>
