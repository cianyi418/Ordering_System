<script setup>
import { ref, onMounted } from 'vue'

const orderId = ref('')
const loading = ref(true)
const error = ref('')
const orderInfo = ref(null)
const orderItems = ref([])
const subtotal = ref(0)
const shippingFee = ref(0)

onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  orderId.value = params.get('order_id') || ''
  if (!orderId.value) {
    error.value = '❗ 找不到訂單編號'
    loading.value = false
    return
  }
  try {
    const res = await fetch('/get-orders')
    const data = await res.json()
    const orders = data.filter(o => o['訂單編號'] === orderId.value)
    if (!orders.length) {
      error.value = '❗ 查無訂單資料'
      loading.value = false
      return
    }
    orderInfo.value = orders[0]
    orderItems.value = []
    subtotal.value = 0
    shippingFee.value = 0
    for (const item of orders) {
      const name = item['商品名稱']
      const qty = Number(item['數量'])
      const price = Number(item['單價'])
      const lineTotal = Number(item['小計金額'])
      if (name === '運費') {
        shippingFee.value += lineTotal
        continue
      }
      subtotal.value += lineTotal
      orderItems.value.push({
        name,
        qty,
        price,
        lineTotal,
      })
    }
  } catch (e) {
    error.value = '❗ 載入失敗'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="max-w-xl mx-auto bg-white rounded-lg shadow p-6 mt-8">
    <h1 class="text-2xl font-bold mb-4 text-center">訂單明細</h1>
    <div v-if="loading" class="text-gray-800">載入中...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else>
      <p class="text-sm text-gray-600">訂單編號：{{ orderId }}</p>
      <p class="text-sm text-gray-600 mb-2">下單時間：{{ orderInfo['訂購時間'] }}</p>

      <hr class="my-2 border-gray-200" />

      <h2 class="font-bold mb-2">商品明細：</h2>
      <table class="w-full text-sm mb-2">
        <tbody>
          <tr v-for="item in orderItems" :key="item.name">
            <td class="py-1">{{ item.name }} x{{ item.qty }}</td>
            <td class="text-right py-1">${{ item.lineTotal }}</td>
          </tr>
        </tbody>
      </table>
      <div class="flex justify-end text-sm mb-1">
        <span>商品小計：</span><span>${{ subtotal }}</span>
      </div>
      <div class="flex justify-end text-sm text-gray-500 mb-1">
        <span>運費：</span><span>${{ shippingFee }}</span>
      </div>

      <hr class="my-2 border-gray-200" />

      <p class="text-sm">取貨方式：{{ orderInfo['取貨方式'] }}</p>
      <p class="text-sm">門市資訊：{{ orderInfo['門市資訊'] }}</p>
      <p class="text-sm mb-2">備註：</p>
      <textarea disabled class="w-full p-2 border rounded bg-gray-50 text-sm mb-4">{{ orderInfo['備註'] || '-' }}</textarea>

      <div class="text-sm flex justify-end mb-1">
        <span>付款狀態：</span>
        <span :class="orderInfo['付款狀態'] === '已付款' ? 'text-green-600' : 'text-red-600'">
          {{ orderInfo['付款狀態'] || '未付款' }}
        </span>
      </div>
      <div class="text-sm flex justify-end mb-1">
        <span>出貨狀態：</span>
        <span :class="orderInfo['出貨狀態'] === '已出貨' ? 'text-green-600' : 'text-red-600'">
          {{ orderInfo['出貨狀態'] || '未出貨' }}
        </span>
      </div>

      <div class="text-right font-bold text-lg mt-2">
        💰 總金額：${{ subtotal + shippingFee }}
      </div>
    </div>
  </div>
</template>