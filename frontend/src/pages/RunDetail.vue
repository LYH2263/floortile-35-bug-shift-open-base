<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const props = defineProps({ id: [String, Number] })
const run = ref(null)
const err = ref('')

onMounted(async () => {
  try {
    run.value = await getJSON(`/api/runs/${props.id}`)
  } catch (e) {
    err.value = e.message
  }
})
</script>
<template>
  <div class="page">
    <h1>记录详情 #{{ id }}</h1>
    <p v-if="err" class="alert">{{ err }}</p>
    <template v-if="run">
      <p><router-link to="/history">← 返回记录列表</router-link></p>
      <div class="hero">{{ run.result?.order_count }} 片</div>
      <table class="tbl detail-tbl">
        <tbody>
          <tr><th>房间</th><td>{{ run.room_name }}</td></tr>
          <tr><th>砖型</th><td>{{ run.tile_name }}</td></tr>
          <tr><th>下单片数</th><td>{{ run.result?.order_count }}</td></tr>
          <tr><th>净用片数</th><td>{{ run.result?.raw_count }}</td></tr>
          <tr><th>实际采用总损耗</th><td>{{ run.waste_pct }}%</td></tr>
          <tr v-if="run.base_waste_pct !== null && run.base_waste_pct !== undefined">
            <th>基础损耗 / 班次加耗</th>
            <td>{{ run.base_waste_pct }}% + {{ run.surcharge_pct }}%
              <span v-if="run.shift_name">（{{ run.shift_name }}）</span>
            </td>
          </tr>
          <tr><th>施工钟点</th>
          <td>{{ run.construction_hour !== null && run.construction_hour !== undefined ? run.construction_hour + ' 时' : '未指定' }}</td></tr>
          <tr><th>测算时间</th><td>{{ run.created_at?.slice(0, 19).replace('T', ' ') }}</td></tr>
          <tr><th>备注</th><td>{{ run.note }}</td></tr>
        </tbody>
      </table>
      <p class="hint">打开详情时按记录字段展示订货片数与所用损耗；班次名称仍取自落库标签。</p>
    </template>
  </div>
</template>
