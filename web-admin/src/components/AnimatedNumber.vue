<template>
  <span>{{ displayValue.toLocaleString() }}</span>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 1000
  }
})

const displayValue = ref(0)

const animate = () => {
  const startValue = displayValue.value
  const endValue = props.value
  const startTime = Date.now()
  
  const update = () => {
    const now = Date.now()
    const progress = Math.min((now - startTime) / props.duration, 1)
    displayValue.value = Math.floor(startValue + (endValue - startValue) * progress)
    
    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }
  
  requestAnimationFrame(update)
}

watch(() => props.value, animate)
onMounted(animate)
</script>
