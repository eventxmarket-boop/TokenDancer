<template>
  <div class="filter-bar">
    <div class="filter-items">
      <slot />
    </div>
    <div v-if="$slots.actions" class="filter-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.filter-items {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  flex-wrap: wrap;
}
.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
</style>
