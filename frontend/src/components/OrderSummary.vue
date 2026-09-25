<script setup>
defineProps({
  result: { type: Object, default: null },
})
</script>
<template>
  <div v-if="result" class="order-summary">
    <div class="hero">{{ result.order_count }} 片</div>
    <ul>
      <li>净用量 {{ result.raw_count }} 片</li>
      <li>
        采用总损耗 {{ result.waste_pct }}%
        <template v-if="result.surcharge_pct > 0">
          （基础 {{ result.base_waste_pct }}% + 班次「{{ result.shift_name }}」加耗 {{ result.surcharge_pct }}%）
        </template>
      </li>
      <li v-if="result.construction_hour !== null && result.construction_hour !== undefined">
        施工钟点 {{ result.construction_hour }} 时
        <span v-if="!result.shift_name">，未命中班次，仅用基础损耗</span>
      </li>
      <li>地面 {{ result.area_m2 }} m²，单砖 {{ result.piece_m2 }} m²</li>
    </ul>
  </div>
</template>
