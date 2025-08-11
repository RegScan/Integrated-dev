<template>
  <el-config-provider :locale="zhCn" :size="size">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { ref } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const size = ref('default')
</script>

<style lang="scss">
#app {
  width: 100%;
  height: 100%;
}
</style>