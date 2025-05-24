import { createRouter, createWebHistory } from "vue-router";
import Order from "./components/Order.vue";
import OrderStatus from "./components/OrderStatus.vue";
import OrderDetail from "./components/OrderDetail.vue";
import Admin from "./components/Admin.vue";

const routes = [
  { path: "/", component: Order },
  { path: "/order-status", component: OrderStatus },
  { path: "/order-detail", component: OrderDetail },
  { path: "/admin", component: Admin },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
