<script setup>
import { onMounted, reactive, ref } from 'vue'
import { deleteJSON, getJSON, postJSON, putJSON } from '../api'

const settings = ref({})
const shifts = ref([])
const err = ref('')
const editingId = ref(null)

const blank = () => ({ name: '夜班', start_hour: 22, end_hour: 6, surcharge_pct: 3, enabled: true })
const form = reactive(blank())

async function load() {
  settings.value = await getJSON('/api/settings')
  shifts.value = (await getJSON('/api/shifts')).items
}
onMounted(load)

function resetForm() {
  editingId.value = null
  Object.assign(form, blank())
  err.value = ''
}

function startEdit(s) {
  editingId.value = s.id
  Object.assign(form, {
    name: s.name,
    start_hour: s.start_hour,
    end_hour: s.end_hour,
    surcharge_pct: s.surcharge_pct,
    enabled: !!s.enabled,
  })
  err.value = ''
}

async function submit() {
  err.value = ''
  const payload = {
    name: form.name,
    start_hour: Number(form.start_hour),
    end_hour: Number(form.end_hour),
    surcharge_pct: Number(form.surcharge_pct),
    enabled: form.enabled,
  }
  try {
    if (editingId.value) {
      await putJSON(`/api/shifts/${editingId.value}`, payload)
    } else {
      await postJSON('/api/shifts', payload)
    }
    resetForm()
    await load()
  } catch (e) {
    err.value = e.message
  }
}

async function toggle(s) {
  await putJSON(`/api/shifts/${s.id}`, { enabled: !s.enabled })
  await load()
}

async function remove(s) {
  if (!confirm(`删除班次「${s.name}」？历史记录不受影响。`)) return
  await deleteJSON(`/api/shifts/${s.id}`)
  if (editingId.value === s.id) resetForm()
  await load()
}

function fmtHour(h) {
  const n = Number(h)
  const hh = String(Math.floor(n)).padStart(2, '0')
  const mm = Math.round((n - Math.floor(n)) * 60)
  return mm ? `${hh}:${String(mm).padStart(2, '0')}` : `${hh}:00`
}
</script>
<template>
  <div class="page">
    <h1>损耗规则</h1>
    <p>默认损耗率按面积法向上取整后再乘 (1+总损耗%)。施工钟点命中启用班次时，总损耗 = 默认损耗 + 班次加耗。</p>
    <p>当前默认损耗：<strong>{{ settings.waste_pct }}%</strong></p>

    <h2>班次加耗</h2>
    <p>钟点范围支持跨午夜（如 22:00–06:00）；起始钟点含、结束钟点不含。加耗不能为负，起止不能相同且须在 0–24 之间。</p>
    <table class="tbl">
      <thead>
        <tr><th>名称</th><th>起始</th><th>结束</th><th>加耗(百分点)</th><th>状态</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="s in shifts" :key="s.id" :class="{ 'shift-off': !s.enabled }">
          <td>{{ s.name }}</td>
          <td>{{ fmtHour(s.start_hour) }}</td>
          <td>{{ fmtHour(s.end_hour) }}</td>
          <td>+{{ s.surcharge_pct }}%</td>
          <td>{{ s.enabled ? '启用中' : '已停用' }}</td>
          <td>
            <button @click="startEdit(s)">编辑</button>
            <button @click="toggle(s)">{{ s.enabled ? '停用' : '启用' }}</button>
            <button @click="remove(s)">删除</button>
          </td>
        </tr>
        <tr v-if="!shifts.length"><td colspan="6">尚无班次，新测算只使用默认损耗。</td></tr>
      </tbody>
    </table>

    <h2>{{ editingId ? '编辑班次' : '新增班次' }}</h2>
    <div class="shift-form">
      <label>名称 <input v-model="form.name" /></label>
      <label>起始钟点 <input v-model.number="form.start_hour" type="number" min="0" max="24" step="0.5" /></label>
      <label>结束钟点 <input v-model.number="form.end_hour" type="number" min="0" max="24" step="0.5" /></label>
      <label>加耗百分点 <input v-model.number="form.surcharge_pct" type="number" min="0" step="0.5" /></label>
      <label class="chk"><input v-model="form.enabled" type="checkbox" /> 启用</label>
      <div>
        <button @click="submit">{{ editingId ? '保存修改' : '添加班次' }}</button>
        <button v-if="editingId" @click="resetForm">取消</button>
      </div>
    </div>
    <p v-if="err" class="alert">保存失败：{{ err }}</p>
  </div>
</template>
