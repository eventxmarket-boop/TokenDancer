<template>
  <div class="product-card card" @click="$router.push(`/products/${product.id}`)">
    <div class="product-img" :style="{ background: imgColor }">
      <span class="product-img-text">商品图片</span>
    </div>
    <div class="product-body">
      <div class="product-top">
        <span v-if="product.tag" class="badge badge-primary product-tag">{{ product.tag }}</span>
        <span class="badge badge-success product-tag" v-if="product.autoDeliver">自动交付</span>
      </div>
      <div class="product-cat">{{ product.category }}</div>
      <h3 class="product-name">{{ product.name }}</h3>
      <div class="product-footer">
        <div class="product-price">
          <span class="price-label">¥</span>
          <span class="price-value">{{ product.price }}</span>
        </div>
        <span class="product-unit">/{{ product.priceUnit ?? product.price_unit ?? '次' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Use a flexible product type to support both mock and real API data
interface FlexibleProduct {
  id: number
  name: string
  category: string
  price: number
  stock?: number
  tag?: string | null
  tagLabel?: string
  priceUnit?: string
  price_unit?: string
  models?: string[]
  autoDeliver?: boolean
}

const props = defineProps<{ product: FlexibleProduct }>()

const colors = ['#EDE9FE', '#DBEAFE', '#D1FAE5', '#FEF3C7', '#FCE7F3', '#E0E7FF']
const imgColor = colors[props.product.id % colors.length]
</script>

<style scoped>
.product-card {
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  padding: 0;
}
.product-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.product-img {
  width: 100%;
  aspect-ratio: 16 / 10;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.product-img-text {
  font-size: 14px;
  color: rgba(0,0,0,0.2);
  font-weight: 600;
}
.product-body {
  padding: 14px 16px;
}
.product-top {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.product-tag {
  font-size: 10px;
  padding: 2px 6px;
}
.product-cat {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
}
.product-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.4;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.product-footer {
  display: flex;
  align-items: baseline;
  gap: 3px;
}
.price-label {
  font-size: 14px;
  font-weight: 700;
  color: #DC2626;
}
.price-value {
  font-size: 20px;
  font-weight: 700;
  color: #DC2626;
}
.product-unit {
  font-size: 11px;
  color: var(--color-text-muted);
}
</style>
