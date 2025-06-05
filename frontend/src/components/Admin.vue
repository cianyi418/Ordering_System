<script setup>
import { ref, reactive, computed, onMounted } from "vue";

const isDev =
  location.hostname.includes("localhost") ||
  location.hostname.startsWith("127.");
const apiBaseUrl = isDev
  ? "http://localhost:8080"
  : "https://orderingsystem-production.up.railway.app";

const passwordInput = ref("");
const authenticated = ref(localStorage.getItem("cozyAdminAuthed") === "true");
const error = ref(false);
const view = ref("orders");
const menu = ref([]);
const orders = ref([]);
const newItem = reactive({ name: "", price: null });
const search = ref("");
const filterPayment = ref("所有付款狀態");
const filterShipping = ref("所有出貨狀態");
const shippingRules = ref({
  "711": { base_fee: 60, cod_extra: 30, free_shipping_item_count: 3 },
  "face_to_face": [{ regions: "", free_shipping_min: 0 }]
});

const shippingOptions = ["未出貨", "已出貨"];
const paymentOptions = ["未付款", "已付款"];

const filteredOrders = computed(() => {
  return orders.value.filter((order) => {
    const keyword = search.value.toLowerCase();
    const matchKeyword =
      order["訂單編號"]?.toLowerCase().includes(keyword) ||
      order["LINE ID"]?.toLowerCase().includes(keyword);
    const matchPayment =
      filterPayment.value === "所有付款狀態" ||
      order["付款狀態"] === filterPayment.value;
    const matchShipping =
      filterShipping.value === "所有出貨狀態" ||
      order["出貨狀態"] === filterShipping.value;
    return matchKeyword && matchPayment && matchShipping;
  });
});

const groupedOrders = computed(() => {
  const groups = {};
  for (const order of filteredOrders.value || []) {
    const id = order["訂單編號"];
    if (!groups[id]) groups[id] = [];
    groups[id].push(order);
  }
  return groups;
});

function buttonClass(tab) {
  return [
    "px-4 py-2 rounded font-medium",
    view.value === tab
      ? "bg-blue-600 text-white"
      : "bg-gray-200 hover:bg-gray-300",
  ];
}

async function checkPassword() {
  const res = await fetch(`${apiBaseUrl}/check-admin-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: passwordInput.value }),
  });
  const result = await res.json();
  if (result.status === "success") {
    localStorage.setItem("cozyAdminAuthed", "true");
    authenticated.value = true;
    error.value = false;
    fetchMenu();
    fetchOrders();
  } else {
    error.value = true;
  }
}

function logout() {
  localStorage.removeItem("cozyAdminAuthed");
  authenticated.value = false;
}

async function fetchMenu() {
  const res = await fetch(`${apiBaseUrl}/menu`);
  menu.value = await res.json();
}

async function fetchOrders() {
  const res = await fetch(`${apiBaseUrl}/get-orders`);
  orders.value = await res.json();
}

function calcOrderTotal(items) {
  return items.reduce((sum, item) => {
    const raw = item["小計金額"] || 0;
    const value = parseInt(raw.toString().replace(/[^\d]/g, "")) || 0;
    return sum + value;
  }, 0);
}

async function addItem() {
  if (!newItem.name.trim() || newItem.price <= 0) {
    alert("請輸入商品名稱與正確價格");
    return;
  }
  const res = await fetch(`${apiBaseUrl}/add-menu-item`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(newItem),
  });
  const result = await res.json();
  alert(result.message);
  if (result.status === "success") {
    fetchMenu();
    newItem.name = "";
    newItem.price = null;
  }
}

async function removeItem(name) {
  if (!confirm(`確定要下架「${name}」嗎？`)) return;
  const res = await fetch(`${apiBaseUrl}/remove-menu-item`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const result = await res.json();
  alert(result.message);
  if (result.status === "success") {
    fetchMenu();
  }
}

async function updatePayment(orderId, newStatus) {
  const res = await fetch(`${apiBaseUrl}/update-payment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId, new_status: newStatus }),
  });
  const result = await res.json();
  if (result.status === "success") {
    const now = new Date().toISOString().slice(0, 19).replace("T", " ");
    orders.value = orders.value.map((order) => {
      if (order["訂單編號"] === orderId) {
        return { ...order, 付款狀態: newStatus, 狀態修改時間: now };
      }
      return order;
    });
  } else {
    alert(`更新失敗：${result.message}`);
  }
}

async function updateShipping(orderId, newStatus) {
  const res = await fetch(`${apiBaseUrl}/update-shipping`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ order_id: orderId, new_status: newStatus }),
  });
  const result = await res.json();
  if (result.status === "success") {
    const now = new Date().toISOString().slice(0, 19).replace("T", " ");
    orders.value.forEach((order) => {
      if (order["訂單編號"] === orderId) {
        order["出貨狀態"] = newStatus;
        order["狀態修改時間"] = now;
      }
    });
  } else {
    alert(`更新失敗：${result.message}`);
  }
}

async function fetchShippingRules() {
  const res = await fetch(`${apiBaseUrl}/shipping-rules`);
  shippingRules.value = await res.json();
}

async function saveShippingRules() {
  const payload = JSON.stringify(shippingRules.value);
  const res = await fetch(`${apiBaseUrl}/shipping-rules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
  });
  const result = await res.json();
  alert(result.message || "運費設定已儲存");
}

function getShippingFee(items) {
  const feeItem = items.find((item) => item["商品名稱"] === "運費");
  return feeItem ? parseInt(feeItem["小計金額"] || 0) : 0;
}

function getSubtotal(items) {
  return items
    .filter((item) => item["商品名稱"] !== "運費")
    .reduce((sum, item) => sum + parseInt(item["小計金額"] || 0), 0);
}

onMounted(() => {
  if (authenticated.value) {
    fetchMenu();
    fetchOrders();
  }
  fetchShippingRules();
});
</script>

<template>
  <div class="bg-gray-50 text-gray-800 min-h-screen">
    <div
      v-if="!authenticated"
      class="min-h-screen flex items-center justify-center"
    >
      <div class="bg-white p-6 rounded shadow max-w-xs w-full">
        <h2 class="text-xl font-semibold mb-4">🔒 請輸入管理密碼</h2>
        <input
          type="password"
          v-model="passwordInput"
          @keyup.enter="checkPassword"
          placeholder="管理密碼"
          class="w-full px-3 py-2 border rounded mb-4"
        />
        <button
          @click="checkPassword"
          class="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          登入
        </button>
        <p v-if="error" class="text-red-500 text-sm mt-2">
          密碼錯誤，請再試一次。
        </p>
      </div>
    </div>

    <div v-else class="max-w-4xl mx-auto p-6">
      <h1 class="text-2xl font-bold mb-4">⚙️ Cozy Eats 後台管理</h1>
      <div class="text-right mb-4">
        <button
          @click="logout"
          class="bg-gray-100 px-3 py-1 text-gray-500 rounded font-bold underline hover:text-red-500"
        >
          登出
        </button>
      </div>

      <div class="mb-6 flex gap-4">
        <button @click="view = 'orders'" :class="buttonClass('orders')">
          訂單管理
        </button>
        <button @click="view = 'menu'" :class="buttonClass('menu')">
          商品管理
        </button>
        <button @click="view = 'shipping'" :class="buttonClass('shipping')">
          運費設定
        </button>
      </div>

      <!-- 訂單管理 -->
      <div v-if="view === 'orders'">
        <div v-for="(orderItems, orderId) in groupedOrders" :key="orderId" class="mb-4">
          <div v-if="orderItems && orderItems.length" class="bg-white rounded shadow p-4">
            <!-- 訂單標題 -->
            <div class="flex justify-between items-center border-b pb-2 mb-2">
              <div>
                <p class="text-xs text-gray-500">訂單編號：{{ orderId }}</p>
                <p class="font-bold text-lg">
                  {{ orderItems[0]?.["LINE ID"] }} - {{ orderItems[0]?.["訂購時間"] }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-blue-600 font-bold text-lg">
                  總額：${{ calcOrderTotal(orderItems) }}
                </p>
                <!-- 付款狀態 -->
                <select
                  v-if="orderItems[0]"
                  v-model="orderItems[0]['付款狀態']"
                  @change="updatePayment(orderId, orderItems[0]['付款狀態'])"
                  :class="[
                    'px-2 py-1 border rounded text-sm focus:outline-none focus:ring cursor-pointer',
                    orderItems[0]['付款狀態'] === '已付款' ||
                    orderItems[0]['付款狀態'] === '貨到付款'
                      ? 'text-green-600 border-green-300 bg-green-50'
                      : 'text-red-600 border-red-300 bg-red-50',
                  ]"
                >
                  <option value="未付款">未付款</option>
                  <option value="已付款">已付款</option>
                  <option value="貨到付款">貨到付款</option>
                </select>
                <!-- 出貨狀態 -->
                <select
                  v-if="orderItems[0]"
                  v-model="orderItems[0]['出貨狀態']"
                  @change="updateShipping(orderId, orderItems[0]['出貨狀態'])"
                  :class="[
                    'px-2 py-1 border rounded text-sm focus:outline-none focus:ring cursor-pointer',
                    orderItems[0]['出貨狀態'] === '已出貨'
                      ? 'text-green-600 border-green-300 bg-green-50'
                      : 'text-red-600 border-red-300 bg-red-50',
                  ]"
                >
                  <option value="未出貨">未出貨</option>
                  <option value="已出貨">已出貨</option>
                  <option value="取消">取消</option>
                </select>
              </div>
            </div>

            <!-- 訂單內容 -->
            <ul class="divide-y">
              <li
                v-for="item in orderItems"
                :key="item['商品名稱']"
                class="py-1 flex justify-between"
              >
                <span>{{ item["商品名稱"] }} x{{ item["數量"] }}</span>
                <span>${{ item["小計金額"] }}</span>
              </li>
            </ul>

            <!-- 備註與其他資訊 -->
            <p class="text-sm text-gray-500 mt-2">
              <span v-if="orderItems[0]?.['備註']" class="block">備註：{{ orderItems[0]["備註"] }}</span>
              <span v-if="orderItems[0]?.['取貨方式']" class="block">取貨方式：{{ orderItems[0]["取貨方式"] }}</span>
              <span v-if="orderItems[0]?.['門市資訊']" class="block">門市資訊：{{ orderItems[0]["門市資訊"] }}</span>
              <span v-if="orderItems[0]?.['狀態修改時間']" class="block">狀態修改：{{ orderItems[0]["狀態修改時間"] }}</span>
            </p>

            <!-- 小計與運費 -->
            <p class="text-sm text-gray-600 mt-2">
              商品小計：${{ getSubtotal(orderItems) }}<br />
              運費：${{ getShippingFee(orderItems) }}
            </p>
          </div>
        </div>
      </div>

      <!-- 商品管理 -->
      <div v-if="view === 'menu'">
        <div class="mb-6 bg-white p-4 rounded shadow">
          <h2 class="text-lg font-semibold mb-2">新增商品</h2>
          <input
            v-model="newItem.name"
            placeholder="商品名稱"
            class="w-full mb-2 px-3 py-2 border rounded"
          />
          <input
            v-model.number="newItem.price"
            type="number"
            placeholder="價格"
            class="w-full mb-2 px-3 py-2 border rounded"
          />
          <button
            @click="addItem"
            class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full"
          >
            上架商品
          </button>
        </div>
        <div class="bg-white p-4 rounded shadow">
          <h2 class="text-lg font-semibold mb-3">目前商品列表</h2>
          <ul class="divide-y">
            <li
              v-for="item in menu"
              :key="item.name"
              class="flex justify-between items-center py-2"
            >
              <span>{{ item.name }}（$ {{ item.price }}）</span>
              <button
                @click="removeItem(item.name)"
                class="bg-red-100 text-red-600 px-3 py-1 rounded hover:bg-red-200"
              >
                下架
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- 運費設定 -->
      <div v-if="view === 'shipping'" class="bg-white p-4 rounded shadow">
        <h2 class="text-lg font-semibold mb-4">運費設定</h2>
        <h3 class="font-bold text-gray-700 mt-4">📦 7-11 運費</h3>
        <label class="block my-2">
          基本運費：<input
            v-model.number="shippingRules['711'].base_fee"
            type="number"
            class="w-24 border px-2 py-1 rounded ml-2"
          />
          元
        </label>
        <label class="block my-2">
          貨到付款手續費：<input
            v-model.number="shippingRules['711'].cod_extra"
            type="number"
            class="w-24 border px-2 py-1 rounded ml-2"
          />
          元
        </label>
        <label class="block my-2">
          幾件免運：<input
            v-model.number="shippingRules['711'].free_shipping_item_count"
            type="number"
            class="w-24 border px-2 py-1 rounded ml-2"
          />
          件
        </label>
        <h3 class="font-bold text-gray-700 mt-6">🤝 面交免運門檻</h3>
        <div
          v-for="(group, index) in shippingRules['face_to_face']"
          :key="index"
          class="mb-4"
        >
          <label>區域：</label>
          <input
            v-model="shippingRules['face_to_face'][index].regions"
            class="border px-2 py-1 w-full rounded mb-1"
            placeholder="以逗號分隔，如：屏東市,長治"
          />
          <label>免運門檻：</label>
          <input
            v-model.number="
              shippingRules['face_to_face'][index].free_shipping_min
            "
            class="border px-2 py-1 w-32 rounded ml-2"
          />
          元
        </div>
        <button
          @click="saveShippingRules"
          class="mt-4 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          💾 儲存設定
        </button>
      </div>
    </div>
  </div>
</template>