<template>
  <div class="max-w-xl mx-auto bg-white rounded-lg shadow p-6">
    <h1 class="text-2xl font-bold mb-4 text-center">訂單明細</h1>
    <div v-if="loading">載入中...</div>
    <div v-else-if="!orderInfo">❗ 查無訂單資料</div>
    <div v-else class="text-gray-800">
      <p class="text-sm text-gray-600">訂單編號：{{ orderId }}</p>
      <p class="text-sm text-gray-600 mb-2">下單時間：{{ orderInfo['訂購時間'] }}</p>

      <div class="border-t border-gray-200 my-2"></div>

      <h2 class="font-bold mb-2">商品明細：</h2>
      <table class="w-full text-sm mb-2">
        <tbody>
          <tr v-for="item in orderItems" :key="item.name">
            <td class="py-1">{{ item.name }} x{{ item.qty }}</td>
            <td class="text-right py-1">${{ item.total }}</td>
          </tr>
        </tbody>
      </table>

      <div class="flex justify-end text-sm mb-2">
        <span>商品小計：</span><span>${{ subtotal }}</span>
      </div>
      <div class="flex justify-end text-sm text-gray-500 mb-2">
        <span>運費：</span><span>${{ shippingFee }}</span>
      </div>

      <div class="border-t border-gray-200 my-2"></div>

      <p class="text-sm">取貨方式：{{ deliveryText }}</p>
      <p class="text-sm">門市資訊：{{ orderInfo['門市資訊'] }}</p>
      <p class="text-sm mb-2">備註：</p>
      <textarea disabled class="w-full p-2 border rounded bg-gray-50 text-sm mb-4">{{ orderInfo['備註'] || '-' }}</textarea>

      <div class="text-sm flex justify-end mb-1">
        <span>付款狀態：</span>
        <span :class="orderInfo['付款狀態'] === '已付款' || '貨到付款' ? 'text-green-600' : 'text-red-600'">
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

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const orderId = route.params.orderId || route.query.order_id || ''
const loading = ref(true)
const orderInfo = ref(null)
const orderItems = ref([])
const subtotal = ref(0)
const shippingFee = ref(0)

const deliveryMap = {
  'pickup': '面交取貨',
  '711-unpaid': '7-11 超商（純取貨）',
  '711-paid': '7-11 超商（取貨付款）'
}

const deliveryText = computed(() =>
  deliveryMap[orderInfo.value?.['取貨方式']] || orderInfo.value?.['取貨方式'] || '-'
)

onMounted(async () => {
  if (!orderId) {
    loading.value = false
    return
  }

  try {
    const res = await fetch('/get-orders')
    const data = await res.json()
    const matchedOrders = data.filter(o => o['訂單編號'] === orderId)

    if (!matchedOrders.length) {
      loading.value = false
      return
    }

    orderInfo.value = matchedOrders[0]
    const items = []
    let sub = 0
    let ship = 0

    for (const item of matchedOrders) {
      const name = item['商品名稱']
      const qty = Number(item['數量'])
      const price = Number(item['單價'])
      const total = Number(item['小計金額'])

      if (name === '運費') {
        ship += total
        continue
      }

      items.push({ name, qty, total })
      sub += total
    }

    orderItems.value = items
    subtotal.value = sub
    shippingFee.value = ship
  } catch (err) {
    console.error('❗ 無法載入訂單資料', err)
  } finally {
    loading.value = false
  }
})
</script>