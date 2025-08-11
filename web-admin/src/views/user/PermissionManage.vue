<template>
  <div class="page-container">
    <h1>{{ pageTitle }}</h1>
    <p>这是 {{ pageTitle }} 页面的占位符。</p>
  </div>
</template>

<script>
export default {
  name: 'PermissionManage',
  data() {
    return {
      pageTitle: '权限管理'
    };
  }
};
</script>

<style scoped>
.page-container {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
h1 {
  color: #333;
  margin-bottom: 15px;
}
p {
  color: #666;
}
</style> 