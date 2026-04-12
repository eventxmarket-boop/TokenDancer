<template>
  <span :class="['status-badge', variantClass]">{{ displayLabel }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
  value?: string | boolean
  label?: string
  type?: 'success' | 'danger' | 'warning' | 'info' | 'default' | 'primary'
}>()

const variantClass = computed(() => {
  if (props.type) return 'badge-' + props.type
  const v = String(props.value ?? '').toLowerCase()
  if (v === 'active' || v === 'enabled' || v === 'used' || v === 'paid' || v === 'success' || v === 'delivered' || v === 'completed') return 'badge-success'
  if (v === 'disabled' || v === 'banned' || v === 'failed' || v === 'refunded' || v === 'expired' || v === 'cancelled' || v === 'invalid' || v === 'banned') return 'badge-danger'
  if (v === 'pending' || v === 'processing' || v === 'on_hold' || v === 'rate_limited') return 'badge-warning'
  if (v === 'inactive' || v === 'draft' || v === 'unused') return 'badge-default'
  return 'badge-info'
})

const displayLabel = computed(() => {
  if (props.label) return props.label
  const v = String(props.value ?? '')
  const map: Record<string, string> = {
    active: '启用', disabled: '停用', enabled: '启用', banned: '封禁',
    pending: '待处理', paid: '已支付', failed: '失败', success: '成功',
    used: '已用', unused: '未用', delivered: '已发货', draft: '草稿',
    completed: '已完成', cancelled: '已取消', refunded: '已退款',
    expired: '已过期', invalid: '无效', processing: '处理中',
    on_hold: '暂停', rate_limited: '触发限流',
  }
  return map[v] ?? v
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.badge-success { background: #f6ffed; color: #52c41a; }
.badge-danger { background: #fff1f0; color: #ff4d4f; }
.badge-warning { background: #fffbe6; color: #faad14; }
.badge-info { background: #e6f7ff; color: #1677ff; }
.badge-default { background: #f5f5f5; color: #888; }
.badge-primary { background: #f0f0ff; color: #5b53ff; }
</style>
