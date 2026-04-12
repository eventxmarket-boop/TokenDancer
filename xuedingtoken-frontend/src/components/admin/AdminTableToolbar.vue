<template>
  <div class="table-toolbar">
    <slot />
  </div>
</template>

<style scoped>
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
