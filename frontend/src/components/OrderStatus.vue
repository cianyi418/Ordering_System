<script setup>
import { ref } from 'vue'

const query = ref('')
const results = ref([])
const loading = ref(false)
const hasSearched = ref(false)

async function search() {
  if (!query.value.trim()) return
  loading.value = true
  hasSearched.value = true
  try {
    const res = await fetch('/get-orders')
    const all = await res.json()
    // filter orders by order number or LINE ID
    const filtered = all.filter(
      o => o['訂單編號'] === query.value || o['LINE ID'] === query.value
    )
    // remove duplicates
    const unique = []
    const seen = new Set()
    for (const row of filtered) {
      if (!seen.has(row['訂單編號'])) {
        unique.push(row)
        seen.add(row['訂單編號'])
      }
    }
    results.value = unique
  } catch (err) {
    console.error('查詢失敗', err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-lg mx-auto p-4 mt-6 bg-white shadow rounded">
    <h1 class="text-xl font-bold mb-4 text-center">訂單查詢</h1>

    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700">請輸入訂單編號或 LINE ID</label>
      <input
        v-model="query"
        @keydown.enter="search"
        type="text"
        class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring focus:ring-indigo-200 focus:outline-none"
      />
      <button
        @click="search"
        class="mt-3 w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
      >查詢</button>
    </div>

    <div v-if="loading" class="text-center text-sm text-gray-500">載入中...</div>

    <div v-if="results.length > 0">
      <div v-for="(order, index) in results" :key="index" class="mb-4 border-b pb-3">
        <p class="text-sm font-medium">訂單編號：{{ order['訂單編號'] }}</p>
        <p class="text-sm text-gray-600">下單時間：{{ order['訂購時間'] }}</p>
        <p class="text-sm">付款狀態：
          <span
            :class="order['付款狀態'] && (order['付款狀態'].includes('已') || order['付款狀態'] === '貨到付款') ? 'text-green-600' : 'text-red-600'"
          >
            {{ order['付款狀態'] }}
          </span>
        </p>
        <p class="text-sm">出貨狀態：
          <span :class="order['出貨狀態'] === '已出貨' ? 'text-green-600' : 'text-red-600'">
            {{ order['出貨狀態'] }}
          </span>
        </p>
        <router-link
          :to="`/order-detail?order_id=${order['訂單編號']}`"
          class="text-blue-500 text-sm underline"
        >查看詳細</router-link>
      </div>
    </div>

    <p
      v-if="!loading && results.length === 0 && hasSearched"
      class="text-center text-sm text-gray-500"
    >查無資料，請確認輸入正確</p>
  </div>
</template>