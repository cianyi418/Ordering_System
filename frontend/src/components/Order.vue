<!-- filepath: frontend/src/components/Order.vue -->
<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'

const isDev = location.hostname === 'localhost' || location.hostname.startsWith('127.')
const apiBaseUrl = isDev
  ? 'http://localhost:8080'
  : 'https://lineapporderingsystem-production.up.railway.app'

const step = ref(0)
const menuData = ref([])
const order = reactive({})
const total = ref(0)
const shippingFee = ref(0)
const uid = ref('')
const userInfo = reactive({ name: '', phone: '', address: '', note: '', store_info: '' })
const orderNote = ref('')
const deliveryOption = ref('')
const currentOrderId = ref('')
const deliveryHint = ref('')
const toastMessage = ref('')
const shippingRules = ref(null)
const submitting = ref(false)

function normalizePhoneToLocal(rawPhone) {
  if (!rawPhone) return ''
  let cleaned = String(rawPhone).replace(/^'+/, '').trim()
  if (/^09\d{8}$/.test(cleaned)) return cleaned
  if (cleaned.startsWith('+886')) return '0' + cleaned.slice(4)
  if (cleaned.startsWith('886') && cleaned.length === 12) return '0' + cleaned.slice(3)
  return cleaned
}
function normalizePhoneToInternational(localPhone) {
  return String(localPhone || '').replace(/^0/, '+886').trim()
}

async function fetchMenu() {
  const response = await fetch(`${apiBaseUrl}/menu`)
  menuData.value = await response.json()
  menuData.value.forEach(item => {
    order[item.name] = { qty: 0, price: item.price }
  })
}
function increaseQty(name) {
  order[name].qty++
  updateTotal()
}
function decreaseQty(name) {
  if (order[name].qty > 0) {
    order[name].qty--
    updateTotal()
  }
}
function updateTotal() {
  total.value = Object.values(order).reduce((sum, item) => sum + item.qty * item.price, 0)
}
async function goToSummary() {
  updateTotal()
  if (total.value === 0) {
    alert('請先選擇商品')
    return
  }
  await updateShippingFee()
  step.value = 1
}
async function updateShippingFee() {
  if (!shippingRules.value || !shippingRules.value['711']) {
    console.warn('🚨 尚未載入運費設定，略過提示文字顯示')
    return
  }
  const itemCount = Object.values(order).reduce((sum, item) => sum + item.qty, 0)
  const deliveryMap = {
    'pickup': '面交（請與客服聯繫面交地點）',
    '711-unpaid': '711 超商（純取貨）',
    '711-paid': '711 超商（取貨付款）'
  }
  const deliveryName = deliveryMap[deliveryOption.value] || ''
  try {
    const res = await fetch(`${apiBaseUrl}/calculate-shipping`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        delivery: deliveryName,
        total_amount: total.value,
        item_count: itemCount,
        district: (userInfo.address || '').trim()
      })
    })
    const result = await res.json()
    shippingFee.value = result.shipping_fee || 0

    if (deliveryOption.value === 'pickup') {
      deliveryHint.value = `🛵 面交門檻：\n- 消費滿 $1000（屏東市、長治、麟洛、西勢、海豐、繁華）\n- 消費滿 $1500（鹽埔、內埔、萬丹、九如、潮州）`
    } else if (deliveryOption.value === '711-unpaid') {
      const base = shippingRules.value['711']?.base_fee || 0
      deliveryHint.value = `冷凍運費 $${base}，全台 7-11 店到店取貨`
    } else if (deliveryOption.value === '711-paid') {
      const base = shippingRules.value['711']?.base_fee || 0
      const cod = shippingRules.value['711']?.cod_extra || 0
      deliveryHint.value = `冷凍運費 $${base + cod}（含貨到付款手續費），全台 7-11 店到店取貨`
    } else {
      deliveryHint.value = ''
    }
  } catch (e) {
    console.error('運費計算失敗:', e)
    alert('⚠️ 無法計算運費，請稍後再試，或確認網路連線')
    shippingFee.value = 0
    deliveryHint.value = ''
  }
}
async function submitOrder() {
  if (!deliveryOption.value) {
    alert('請選擇取貨方式')
    return
  }
  await updateShippingFee()
  step.value = 2
}
function showToast(msg, duration = 3000) {
  toastMessage.value = msg
  setTimeout(() => {
    toastMessage.value = ''
  }, duration)
}
async function submitFinalOrder() {
  userInfo.phone = normalizePhoneToLocal(userInfo.phone)
  if (submitting.value) return
  submitting.value = true

  if (!uid.value) {
    alert('尚未取得 LINE 使用者資訊，請稍候或重新整理頁面')
    submitting.value = false
    return
  }
  if (!userInfo.name || !userInfo.phone) {
    alert('請填寫姓名與電話')
    submitting.value = false
    return
  }
  if (!/^09\d{8}$/.test(userInfo.phone)) {
    alert('請輸入有效的手機號碼（例如：09xxxxxxxx）')
    submitting.value = false
    return
  }

  let userName = '測試用戶'
  if (!isDev) {
    const profile = await window.liff.getProfile()
    userName = profile.displayName
  }

  const now = new Date()
  const timestamp = now.getTime()
  const random4 = Math.floor(1000 + Math.random() * 9000)
  const orderId = `ORDER-${timestamp}-${random4}`
  currentOrderId.value = orderId

  const order_items = Object.entries(order)
    .filter(([name, item]) => item.qty > 0)
    .map(([name, item]) => ({
      product: name,
      qty: item.qty,
      price: item.price
    }))
  if (order_items.length === 0) {
    alert('請先選擇商品')
    submitting.value = false
    return
  }
  addShippingItem(order_items)

  if (deliveryOption.value.includes('711') && !userInfo.store_info) {
    alert('請填寫 7-11 店名或店號')
    submitting.value = false
    return
  }

  const orderData = {
    user: userName,
    order_id: orderId,
    user_id: uid.value,
    note: (orderNote.value || '').trim(),
    delivery: deliveryOption.value,
    store_info: userInfo.store_info || '',
    order_items
  }

  const res = await fetch(`${apiBaseUrl}/order`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  })
  if (!res.ok) {
    alert('訂單送出失敗，請稍後再試')
    submitting.value = false
    return
  }

  const userInfoData = {
    order_id: orderId,
    user_id: uid.value,
    ...userInfo,
    phone: normalizePhoneToInternational(userInfo.phone)
  }
  await fetch(`${apiBaseUrl}/user-info`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userInfoData)
  })

  await new Promise(resolve => setTimeout(resolve, 500))
  showToast('資料已送出，感謝您的訂購')
  resetOrder()
  submitting.value = false
}
function resetOrder() {
  for (const item in order) {
    order[item].qty = 0
  }
  updateTotal()
  userInfo.name = ''
  userInfo.phone = ''
  userInfo.address = ''
  userInfo.note = ''
  userInfo.store_info = ''
  orderNote.value = ''
  deliveryOption.value = ''
  currentOrderId.value = ''
  step.value = 0
  submitting.value = false
}
async function prefillUserInfo() {
  if (!uid.value) return
  try {
    const res = await fetch(`${apiBaseUrl}/get-user?uid=${uid.value}`)
    const result = await res.json()
    if (result.status === 'success' && result.data) {
      const data = result.data
      const phone = normalizePhoneToLocal(data.phone)
      if (!/^09\d{8}$/.test(userInfo.phone) && /^09\d{8}$/.test(phone)) {
        userInfo.phone = phone
      }
      if (!userInfo.name) userInfo.name = data.name || ''
      if (!userInfo.address) userInfo.address = data.address || ''
      if (!userInfo.note) userInfo.note = data.note || ''
      if (!userInfo.store_info) userInfo.store_info = data.store_info || ''
    }
  } catch (err) {
    console.warn('[預填失敗]', err)
  }
}
async function fetchShippingRules() {
  const res = await fetch(`${apiBaseUrl}/shipping-rules`)
  shippingRules.value = await res.json()
}
function addShippingItem(orderItems) {
  const alreadyHasShipping = orderItems.some(item => item.product === '運費')
  if (!alreadyHasShipping && shippingFee.value > 0) {
    orderItems.push({
      product: '運費',
      qty: 1,
      price: shippingFee.value
    })
  }
  return orderItems
}

// localStorage 同步
watch(userInfo, (val) => {
  localStorage.setItem('userInfo', JSON.stringify(val))
}, { deep: true })

onMounted(async () => {
  submitting.value = false
  await fetchShippingRules()
  // localStorage 預填
  const stored = JSON.parse(localStorage.getItem('userInfo') || '{}')
  if (!/^09\d{8}$/.test(stored.phone || '')) {
    stored.phone = ''
  }
  Object.assign(userInfo, {
    name: stored.name || '',
    phone: stored.phone || '',
    address: stored.address || '',
    note: stored.note || '',
    store_info: stored.store_info || ''
  })
  await fetchMenu()
  if (isDev) {
    const testUidRes = await fetch(`${apiBaseUrl}/test-uid`)
    const testUidData = await testUidRes.json()
    uid.value = testUidData.uid || ''
    await prefillUserInfo()
    return
  }
  try {
    const liffId = window.APP_CONFIG?.liffId || ''
    await window.liff.init({ liffId })
    if (!liffId) {
      console.error("❗ 找不到 LIFF ID，請確認 static/config.js 是否有正確設定")
    }
    if (!window.liff.isLoggedIn()) {
      window.liff.login()
      return
    }
    const profile = await window.liff.getProfile()
    uid.value = profile.userId
    await prefillUserInfo()
  } catch (err) {
    console.error('⚠️ LIFF 初始化失敗', err)
  }
  fetchShippingRules()
})
</script>

<template>
  <!-- <router-link to="/order-status">訂單查詢</router-link> -->
  <div class="max-w-md mx-auto p-4 bg-white shadow">
    <!-- Loading Overlay -->
    <div v-if="submitting" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
      <div class="bg-white p-6 rounded shadow text-center">
        <p class="text-lg font-semibold mb-2">訂單送出中...</p>
        <svg class="animate-spin h-6 w-6 text-blue-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none"
          viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z">
          </path>
        </svg>
      </div>
    </div>

    <template v-if="step === 0">
      <h1 class="text-2xl font-bold mb-4 w-full text-center">老宅私廚</h1>
      <h2 class="text-xl font-bold mb-2">選擇商品</h2>
      <p class="text-sm text-gray-500 mb-2">水餃 1包/ 30入</p>
      <div v-for="item in menuData" :key="item.name" class="mb-2">
        <div class="flex justify-between items-center">
          <span>{{ item.name }} (${{ item.price }})</span>
          <div class="flex items-center space-x-2">
            <button @click="decreaseQty(item.name)"
              class="bg-orange-100 hover:bg-orange-300 px-2 rounded">-</button>
            <span>{{ order[item.name]?.qty || 0 }}</span>
            <button @click="increaseQty(item.name)"
              class="bg-blue-100 hover:bg-blue-300 px-2 rounded">+</button>
          </div>
        </div>
      </div>
      <button class="mt-4 w-full bg-blue-500 text-white py-2 rounded" @click="goToSummary">下一步</button>
    </template>

    <template v-else-if="step === 1">
      <h2 class="text-xl font-bold mb-2">訂單明細</h2>
      <hr class="border-gray-300 border-2 my-3" />
      <ul>
        <template v-for="(item, name) in order" :key="name">
          <li v-if="item.qty > 0" class="flex justify-between">
            <span>{{ name }} x{{ item.qty }}</span>
            <span>${{ item.qty * item.price }}</span>
          </li>
        </template>
      </ul>
      <p class="mt-2 text-right">小計：${{ total }}</p>
      <p class="mt-4 text-right text-m text-gray-600">運費：${{ shippingFee }}</p>
      <p class="text-right">總計：${{ total + shippingFee }}</p>
      <textarea v-model="orderNote" maxlength="100" placeholder="備註 (選填，最多 100 字)"
        class="w-full border mt-2 px-2 py-1 rounded"></textarea>
      <p class="text-sm text-gray-500 text-right">
        {{ orderNote.length }}/100 字
      </p>
      <select v-model="deliveryOption" @change="updateShippingFee" class="w-full mt-2 border px-2 py-1 rounded">
        <option disabled value="">選擇取貨方式</option>
        <option value="pickup">面交（請與客服聯繫面交地點）</option>
        <option value="711-unpaid">711 超商（純取貨）</option>
        <option value="711-paid">711 超商（取貨付款）</option>
      </select>
      <p v-if="deliveryHint" class="text-sm text-gray-600 mt-2 whitespace-pre-line">
        {{ deliveryHint }}
      </p>
      <div class="flex justify-between mt-4">
        <button @click="step--"
          class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded">
          上一步
        </button>
        <button @click="submitOrder"
          class="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded">
          下一步
        </button>
      </div>
    </template>

    <template v-else-if="step === 2">
      <h2 class="text-lg font-bold mb-2">訂購人資料</h2>
      <input v-model="userInfo.name" placeholder="姓名" class="w-full border mb-2 px-3 py-2 rounded" />
      <input v-model="userInfo.phone" type="text" inputmode="numeric" pattern="[0-9]*" placeholder="電話"
        class="w-full border mb-2 px-3 py-2 rounded" />
      <input v-model="userInfo.address" placeholder="地址" class="w-full border mb-2 px-3 py-2 rounded" />
      <input v-if="deliveryOption.includes('711')" v-model="userInfo.store_info" placeholder="請輸入 7-11 店名或店號"
        class="w-full border mb-2 px-3 py-2 rounded" />
      <div class="flex justify-between mt-4">
        <button @click="step--"
          class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded">
          上一步
        </button>
        <button @click="submitFinalOrder" :disabled="submitting"
          class="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50">
          送出訂單
        </button>
      </div>
    </template>

    <!-- Toast -->
    <div v-if="toastMessage"
      class="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 bg-green-600 text-white px-4 py-2 rounded shadow transition-opacity duration-300">
      {{ toastMessage }}
    </div>
  </div>
</template>