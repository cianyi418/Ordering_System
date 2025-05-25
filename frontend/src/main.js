import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./index.css";

async function initApp() {
  // Check if LIFF SDK is loaded
  if (!window.liff) {
    console.error("❗ LIFF SDK 尚未載入，請確認 index.html 有載入 sdk.js");
    return;
  }

  try {
    await window.liff.init({
      liffId: import.meta.env.VITE_LIFF_ID, // recieive LIFF ID from environment variables
    });
    console.log("VITE_LIFF_ID =", import.meta.env.VITE_LIFF_ID);

    console.log("✅ LIFF 初始化成功", window.liff.getContext());

    // Initialize Vue app after LIFF is ready
    createApp(App).use(router).mount("#app");
  } catch (err) {
    console.error("❌ LIFF 初始化失敗", err);
  }
}

initApp();
