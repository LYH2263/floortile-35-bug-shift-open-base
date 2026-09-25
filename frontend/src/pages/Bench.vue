<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import OrderSummary from '../components/OrderSummary.vue'
import TileGridPreview from '../components/TileGridPreview.vue'

const rooms = ref([])
const tiles = ref([])
const roomId = ref(1)
const tileId = ref(1)
const useHour = ref(false)
const constructionHour = ref(22)
const result = ref(null)
const err = ref('')

onMounted(async () => {
  rooms.value = (await getJSON('/api/rooms')).items.filter(r => r.data_quality === 'clean')
  tiles.value = (await getJSON('/api/tiles')).items.filter(t => t.data_quality === 'clean')
  if (rooms.value.length) roomId.value = rooms.value[0].id
  if (tiles.value.length) tileId.value = tiles.value[0].id
})

function hourParam() {
  return useHour.value ? `&construction_hour=${Number(constructionHour.value)}` : ''
}

async function preview() {
  err.value = ''
  try {
    result.value = await getJSON(
      `/api/estimate?room_id=${roomId.value}&tile_id=${tileId.value}${hourParam()}`
    )
  } catch (e) {
    err.value = e.message
    result.value = null
  }
}

async function saveRun() {
  err.value = ''
  try {
    result.value = await postJSON('/api/estimate', {
      room_id: roomId.value,
      tile_id: tileId.value,
      construction_hour: useHour.value ? Number(constructionHour.value) : null,
      save: true,
      note: '前端保存',
    })
  } catch (e) {
    err.value = e.message
  }
}
</script>
<template>
  <div class="page">
    <h1>下单测算</h1>
    <label>房间 <select v-model.number="roomId"><option v-for="r in rooms" :key="r.id" :value="r.id">{{ r.name }}</option></select></label>
    <label>砖型 <select v-model.number="tileId"><option v-for="t in tiles" :key="t.id" :value="t.id">{{ t.name }}</option></select></label>
    <label class="chk"><input type="checkbox" v-model="useHour" /> 指定施工钟点</label>
    <label v-if="useHour">
      施工钟点
      <input v-model.number="constructionHour" type="number" min="0" max="24" step="0.5" />
      <span class="hint">（0–24，含小数；如 23.5 即 23:30）</span>
    </label>
    <button @click="preview">试算</button>
    <button @click="saveRun">保存记录</button>
    <p v-if="err" class="alert">{{ err }}</p>
    <OrderSummary :result="result" />
    <TileGridPreview v-if="result?.layout" :cols="result.layout.cols" :rows="result.layout.rows" :grid-count="result.layout.grid_count" />
  </div>
</template>
