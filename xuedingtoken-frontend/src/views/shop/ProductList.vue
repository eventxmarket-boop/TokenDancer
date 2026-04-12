<template>
  <div class="product-list-page">
    <ShopNav />

    <div class="container page-content">
      <div class="page-header">
        <h1 class="section-title">商品中心</h1>
        <p class="section-desc">浏览我们的精选商品</p>
      </div>

      <!-- Category filter tags -->
      <div class="filter-bar">
        <div class="category-tags">
          <button
            v-for="cat in categories"
            :key="cat"
            class="cat-tag"
            :class="{ active: selectedCategory === cat }"
            @click="selectCategory(cat)"
          >
            {{ cat }}
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-wrap">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-wrap card">
        <div class="error-icon">⚠️</div>
        <p>{{ error }}</p>
        <button class="btn btn-outline btn-sm mt-4" @click="fetchProducts">重试</button>
      </div>

      <!-- Products grid -->
      <div v-else-if="paginatedProducts.length === 0" class="empty-wrap">
        <BaseEmpty icon="📦" title="暂无商品" desc="该分类下暂无商品" />
      </div>

      <div v-else class="products-grid">
        <router-link
          v-for="p in paginatedProducts"
          :key="p.id"
          :to="`/products/${p.id}`"
          class="product-card-link"
        >
          <ProductCard :product="p" />
        </router-link>
      </div>

      <!-- Pagination -->
      <BasePagination
        v-model:current="currentPage"
        :total="totalPages"
      />
    </div>

    <!-- Floating cart -->
    <router-link to="/cart" class="floating-cart">
      <span class="cart-icon">🛒</span>
      <span v-if="cartCount > 0" class="cart-badge">{{ cartCount }}</span>
    </router-link>

    <ShopFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ShopNav from '@/components/shop/ShopNav.vue'
import ShopFooter from '@/components/shop/ShopFooter.vue'
import ProductCard from '@/components/shop/ProductCard.vue'
import BasePagination from '@/components/common/BasePagination.vue'
import { productsApi } from '@/api/products'
import { useCartStore } from '@/stores/cart'

interface Product {
  id: number
  name: string
  slug: string
  category: string
  tag: string | null
  price_cny: number
  stock: number
  delivery_type: string
  is_active: boolean
  sort_order: number
  // mapped for display
  price: number
  price_unit: string
  models?: string[]
  autoDeliver?: boolean
}

const products = ref<Product[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const selectedCategory = ref('全部')
const currentPage = ref(1)
const perPage = 9

const categories = computed(() => {
  const cats = new Set(products.value.map(p => p.category))
  return ['全部', ...Array.from(cats)]
})

const filteredProducts = computed(() => {
  return selectedCategory.value === '全部'
    ? products.value
    : products.value.filter(p => p.category === selectedCategory.value)
})

const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * perPage
  return filteredProducts.value.slice(start, start + perPage)
})

const totalPages = computed(() => Math.ceil(filteredProducts.value.length / perPage))

const selectCategory = (cat: string) => {
  selectedCategory.value = cat
  currentPage.value = 1
  fetchProducts()
}

const cartStore = useCartStore()
const cartCount = computed(() => cartStore.totalItems)

const fetchProducts = async () => {
  loading.value = true
  error.value = null
  try {
    const params: Record<string, string> = {}
    if (selectedCategory.value !== '全部') params.category = selectedCategory.value
    const raw = await productsApi.list(params)
    products.value = raw.map((p) => ({
      ...p,
      price: p.price_cny,
      price_unit: p.delivery_type === 'auto' ? '次' : '份',
      autoDeliver: p.delivery_type === 'auto',
    }))
  } catch (e: any) {
    error.value = e.message || '加载商品失败'
  } finally {
    loading.value = false
  }
}

onMounted(fetchProducts)
</script>

<style scoped>
.page-content {
  padding-top: 32px;
  padding-bottom: 32px;
}
.page-header {
  margin-bottom: 32px;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
}
.category-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.cat-tag {
  padding: 6px 16px;
  border-radius: 99px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.cat-tag:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.cat-tag.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
.loading-wrap {
  text-align: center;
  padding: 64px 0;
  color: var(--color-text-secondary);
}
.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-wrap {
  text-align: center;
  padding: 64px 0;
}
.error-icon { font-size: 48px; opacity: 0.5; margin-bottom: 12px; }
.empty-wrap { padding: 32px 0; }
.products-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.product-card-link {
  text-decoration: none;
  display: block;
  transition: transform 0.2s, box-shadow 0.2s;
}
.product-card-link:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}
.floating-cart {
  position: fixed;
  right: 24px;
  bottom: 80px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  box-shadow: var(--shadow-md);
  z-index: 50;
  transition: all 0.2s;
}
.floating-cart:hover {
  background: var(--color-primary-dark);
  transform: scale(1.05);
}
.floating-cart .cart-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--color-danger);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
