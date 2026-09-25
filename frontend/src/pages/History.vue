<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
</script>
<template>
  <div class="page">
    <h1>测算记录</h1>
    <table class="tbl">
      <thead><tr><th>编号</th><th>时间</th><th>房间</th><th>砖型</th><th>片数</th><th>班次</th></tr></thead>
      <tbody>
        <tr v-for="r in items" :key="r.id">
          <td><router-link :to="`/runs/${r.id}`">#{{ r.id }}</router-link></td>
          <td>{{ r.created_at?.slice(0, 19) }}</td>
          <td>{{ r.room_name }}</td>
          <td>{{ r.tile_name }}</td>
          <td>{{ r.result?.order_count }}</td>
          <td>{{ r.shift_name || '白天' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
