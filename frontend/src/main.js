import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./index.css";

async function initApp() {
  if (!window.liff) {
    console.error("❗ LIFF SDK 尚未載入，請確認 index.html 有載入 sdk.js");
    return;
  }

  const liffId = import.meta.env.VITE_LIFF_ID || window.APP_CONFIG?.liffId;
  if (!liffId) {
    console.error("❌ 無法取得 LIFF ID，請確認 config.js 是否正確載入");
    return;
  }

  try {
    await window.liff.init({ liffId });
    console.log("✅ LIFF 初始化成功", window.liff.getContext());

    // Automatically direct order-detail (if there is order_id)
    const params = new URLSearchParams(window.location.search);
    const orderId = params.get("order_id");
    if (orderId && window.location.pathname === "/") {
      router.replace(`/order-detail?order_id=${orderId}`);
    }

    createApp(App).use(router).mount("#app");
  } catch (err) {
    console.error("❌ LIFF 初始化失敗", err);
  }
}

initApp();
