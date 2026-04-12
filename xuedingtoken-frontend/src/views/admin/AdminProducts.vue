<template>
  <div class="page-container">
    <div class="page-title-row">
      <h1 class="page-title">商品管理</h1>
      <div class="title-actions">
        <button class="btn-outline-sm" @click="fetchProducts">🔄 刷新</button>
        <button class="btn-primary" @click="openCreate">+ 新增商品</button>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <div v-if="showForm" class="modal-mask">
      <div class="modal-box modal-box-lg">
        <h3 class="modal-title">{{ editingId ? '编辑商品' : '新增商品' }}</h3>
        <div class="form-grid">
          <div class="form-group span2">
            <label>商品名称 <span class="required">*</span></label>
            <input class="form-input" v-model="form.name" placeholder="如：Claude Pro 月卡" />
          </div>
          <div class="form-group">
            <label>Slug <span class="required">*</span></label>
            <input class="form-input" v-model="form.slug" placeholder="如：claude-pro-monthly" :disabled="!!editingId" />
          </div>
          <div class="form-group">
            <label>分类 <span class="required">*</span></label>
            <input class="form-input" v-model="form.category" placeholder="如：会员服务" list="category-list" />
            <datalist id="category-list">
              <option v-for="cat in allCategories" :key="cat" :value="cat" />
            </datalist>
          </div>
          <div class="form-group">
            <label>标签（可选）</label>
            <input class="form-input" v-model="form.tag" placeholder="如：热销" />
          </div>
          <div class="form-group">
            <label>价格 CNY <span class="required">*</span></label>
            <input type="number" class="form-input" v-model.number="form.price_cny" placeholder="0.00" step="0.01" />
          </div>
          <div class="form-group">
            <label>USD 参考值</label>
            <input type="number" class="form-input" v-model.number="form.price_usd_value" placeholder="0.00" step="0.01" />
          </div>
          <div class="form-group">
            <label>库存</label>
            <input type="number" class="form-input" v-model.number="form.stock" placeholder="-1 表示无限" />
          </div>
          <div class="form-group">
            <label>发货方式</label>
            <select class="form-select" v-model="form.delivery_type">
              <option value="auto">自动发货</option>
              <option value="manual">手动处理</option>
            </select>
          </div>
          <div class="form-group">
            <label>商品类型</label>
            <select class="form-select" v-model="form.product_type">
              <option value="balance_topup">余额充值</option>
              <option value="subscription">订阅套餐</option>
              <option value="token_pack">Token包</option>
            </select>
          </div>
          <div class="form-group">
            <label>订阅天数</label>
            <input type="number" class="form-input" v-model.number="form.subscription_days" placeholder="如：30" />
          </div>
          <div class="form-group">
            <label>Token配额</label>
            <input type="number" class="form-input" v-model.number="form.token_quota" placeholder="如：100000" />
          </div>
          <div class="form-group">
            <label>排序值</label>
            <input type="number" class="form-input" v-model.number="form.sort_order" placeholder="0" />
          </div>
          <div class="form-group">
            <label>上架状态</label>
            <select class="form-select" v-model="form.is_active">
              <option :value="true">上架</option>
              <option :value="false">下架</option>
            </select>
          </div>
          <div class="form-group span2">
            <label>商品描述</label>
            <textarea class="form-textarea" v-model="form.description" placeholder="商品详细描述…" rows="3" />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-outline" @click="closeForm">取消</button>
          <button class="btn-primary" @click="handleSave" :disabled="saving">
            {{ saving ? '保存中…' : (editingId ? '保存修改' : '确认创建') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 列表 -->
    <AdminSectionCard>
      <AdminTableToolbar>
        <AdminFilterBar>
          <input class="filter-input" placeholder="搜索商品名称" v-model="filters.search" @input="debouncedFetch" />
          <select class="filter-select" v-model="filters.category" @change="fetchProducts">
            <option value="">全部分类</option>
            <option v-for="cat in allCategories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
          <select class="filter-select" v-model="filters.is_active" @change="fetchProducts">
            <option value="">全部状态</option>
            <option :value="true">上架</option>
            <option :value="false">下架</option>
          </select>
        </AdminFilterBar>
      </AdminTableToolbar>

      <div class="table-wrap">
        <table class="admin-table">
          <thead><tr>
            <th>ID</th><th>商品名称</th><th>分类</th><th>标签</th>
            <th>价格(CNY)</th><th>库存</th><th>发货</th>
            <th>类型</th><th>排序</th><th>状态</th><th>操作</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="11" class="td-center td-pad">加载中…</td></tr>
            <tr v-else-if="error"><td colspan="11" class="td-center td-pad td-error">{{ error }}</td></tr>
            <tr v-else-if="products.length === 0"><td colspan="11" class="td-center td-pad"><AdminEmptyState icon="📦" title="暂无商品" /></td></tr>
            <tr v-else v-for="p in products" :key="p.id" class="tr-body">
              <td>{{ p.id }}</td>
              <td class="td-bold">{{ p.name }}</td>
              <td>{{ p.category || '—' }}</td>
              <td>{{ p.tag ? '🏷️ ' + p.tag : '—' }}</td>
              <td class="td-price">¥{{ typeof p.price_cny === 'number' ? p.price_cny.toFixed(2) : p.price_cny }}</td>
              <td>{{ p.stock < 0 ? '∞' : p.stock }}</td>
              <td><span class="badge-delivery">{{ p.delivery_type === 'auto' ? '自动' : '手动' }}</span></td>
              <td><span class="type-tag">{{ typeLabel(p.product_type) }}</span></td>
              <td>{{ p.sort_order ?? 0 }}</td>
              <td><AdminStatusBadge :value="p.is_active ? 'active' : 'inactive'" /></td>
              <td>
                <div class="td-actions">
                  <button class="btn-action-sm" @click="openEdit(p)">编辑</button>
                  <button v-if="p.is_active" class="btn-warning-sm" @click="toggleActive(p)">下架</button>
                  <button v-else class="btn-success-sm" @click="toggleActive(p)">上架</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-bar">
        <span class="page-info">共 {{ products.length }} 条</span>
      </div>
    </AdminSectionCard>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import AdminSectionCard from '@/components/admin/AdminSectionCard.vue'
import AdminTableToolbar from '@/components/admin/AdminTableToolbar.vue'
import AdminFilterBar from '@/components/admin/AdminFilterBar.vue'
import AdminStatusBadge from '@/components/admin/AdminStatusBadge.vue'
import AdminEmptyState from '@/components/admin/AdminEmptyState.vue'
import { adminProductsApi } from '@/api/admin'
import { useFeedbackStore } from '@/stores/feedback'

const feedback = useFeedbackStore()
const products = ref<any[]>([])
const allCategories = ref<string[]>([])
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const filters = reactive({ search: '', category: '', is_active: '' })
const typeLabel = (t: string) => ({ balance_topup:'余额充值', subscription:'订阅套餐', token_pack:'Token包' }[t] || t)

const defaultForm = () => ({
  name: '', slug: '', category: '', tag: '', description: '',
  price_cny: 0, price_usd_value: 0, stock: -1,
  delivery_type: 'auto', product_type: 'balance_topup',
  subscription_days: 0, token_quota: 0,
  is_active: true, sort_order: 0,
})
const form = reactive(defaultForm())

const allCategoriesComputed = computed(() => {
  const cats = new Set(products.value.map((p: any) => p.category).filter(Boolean))
  allCategories.value = Array.from(cats) as string[]
  return allCategories.value
})

let debounceTimer: ReturnType<typeof setTimeout>
const debouncedFetch = () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(fetchProducts, 350) }

const fetchProducts = async () => {
  loading.value = true; error.value = ''
  try {
    const params: any = {}
    if (filters.search) params.search = filters.search
    if (filters.category) params.category = filters.category
    if (filters.is_active !== '') params.is_active = filters.is_active === 'true'
    products.value = await adminProductsApi.list(params)
    allCategoriesComputed.value // compute categories
  } catch (e: any) {
    error.value = '加载失败：' + (e.message || '未知错误'); products.value = []
  } finally { loading.value = false }
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, defaultForm())
  showForm.value = true
}

const openEdit = (p: any) => {
  editingId.value = p.id
  Object.assign(form, {
    name: p.name, slug: p.slug, category: p.category || '', tag: p.tag || '',
    description: p.description || '', price_cny: p.price_cny, price_usd_value: p.price_usd_value,
    stock: p.stock, delivery_type: p.delivery_type,
    product_type: p.product_type || 'balance_topup',
    subscription_days: p.subscription_days || 0,
    token_quota: p.token_quota || 0,
    is_active: p.is_active, sort_order: p.sort_order ?? 0,
  })
  showForm.value = true
}

const closeForm = () => {
  showForm.value = false; editingId.value = null; Object.assign(form, defaultForm())
}

const handleSave = async () => {
  if (!form.name?.trim()) { feedback.warning('请填写商品名称'); return }
  if (!form.slug?.trim()) { feedback.warning('请填写 slug'); return }
  if (!form.category?.trim()) { feedback.warning('请填写分类'); return }
  saving.value = true
  try {
    if (editingId.value) {
      await adminProductsApi.update(editingId.value, { ...form })
    } else {
      await adminProductsApi.create({ ...form })
    }
    closeForm()
    feedback.success(editingId.value ? '商品已更新' : '商品已创建')
    fetchProducts()
  } catch (e: any) { feedback.error(e.message || '保存失败') }
  finally { saving.value = false }
}

const toggleActive = async (p: any) => {
  try {
    await adminProductsApi.update(p.id, { is_active: !p.is_active })
    p.is_active = !p.is_active
    feedback.success(p.is_active ? '已上架' : '已下架')
  } catch (e: any) { feedback.error(e.message || '操作失败') }
}

fetchProducts()
</script>

<style scoped>
.page-container {}
.page-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.page-title { font-size:20px; font-weight:700; color:#1a1a2e; }
.title-actions { display:flex; gap:10px; align-items:center; }
.btn-outline-sm { font-size:12px; padding:6px 14px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }
.btn-primary { font-size:13px; padding:8px 18px; background:#1677ff; color:#fff; border:none; border-radius:6px; cursor:pointer; }
.btn-primary:hover { background:#4096ff; }
.btn-primary:disabled { opacity:0.6; cursor:not-allowed; }

.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center; z-index:1000; overflow-y:auto; padding:20px; }
.modal-box-lg { background:#fff; border-radius:12px; padding:28px; width:680px; max-width:100%; box-shadow:0 8px 32px rgba(0,0,0,0.15); }
.modal-title { font-size:16px; font-weight:700; margin:0 0 20px; color:#1a1a2e; }
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.span2 { grid-column:1 / -1; }
.required { color:#ff4d4f; }
.form-group label { display:block; font-size:12px; color:#666; margin-bottom:4px; font-weight:600; }
.form-input, .form-select, .form-textarea { width:100%; font-size:13px; padding:8px 10px; border:1px solid #e8e8e8; border-radius:6px; outline:none; color:#333; box-sizing:border-box; background:#fff; }
.form-input:focus, .form-select:focus, .form-textarea:focus { border-color:#1677ff; }
.form-input:disabled { background:#f5f5f5; color:#999; }
.form-textarea { resize:vertical; min-height:80px; }
.modal-actions { display:flex; justify-content:flex-end; gap:12px; margin-top:20px; }
.btn-outline { font-size:13px; padding:8px 18px; background:#fff; color:#666; border:1px solid #d9d9d9; border-radius:6px; cursor:pointer; }

.table-wrap { overflow-x:auto; }
.admin-table { width:100%; border-collapse:collapse; font-size:13px; }
.admin-table th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#999; text-transform:uppercase; letter-spacing:0.5px; background:#fafafa; border-bottom:1px solid #f0f0f0; white-space:nowrap; }
.admin-table td { padding:10px 14px; border-bottom:1px solid #f5f5f5; color:#333; }
.tr-body:hover td { background:#fafafa; }
.tr-body:last-child td { border-bottom:none; }
.td-center { text-align:center; }
.td-pad { padding:32px !important; }
.td-error { color:#ff4d4f; }
.td-bold { font-weight:600; }
.td-price { font-weight:600; color:#1677ff; }
.badge-delivery { font-size:11px; padding:2px 7px; background:#f0f0ff; color:#5b53ff; border-radius:10px; font-weight:600; }
.td-actions { display:flex; gap:6px; }
.btn-action-sm { font-size:11px; padding:3px 8px; color:#1677ff; background:none; border:1px solid #1677ff; border-radius:4px; cursor:pointer; }
.btn-action-sm:hover { background:#e6f7ff; }
.btn-warning-sm { font-size:11px; padding:3px 8px; color:#faad14; background:none; border:1px solid #faad14; border-radius:4px; cursor:pointer; }
.btn-warning-sm:hover { background:#fffbe6; }
.btn-success-sm { font-size:11px; padding:3px 8px; color:#52c41a; background:none; border:1px solid #52c41a; border-radius:4px; cursor:pointer; }
.btn-success-sm:hover { background:#f6ffed; }

.filter-input, .filter-select { font-size:13px; padding:6px 10px; border:1px solid #e8e8e8; border-radius:6px; background:#fff; outline:none; color:#333; }
.filter-input:focus, .filter-select:focus { border-color:#1677ff; }
.filter-input { min-width:160px; }

.pagination-bar { display:flex; align-items:center; justify-content:flex-end; padding:12px 20px; border-top:1px solid #f0f0f0; }
.page-info { font-size:13px; color:#888; }
.type-tag { font-size:11px; color:#888; }
</style>
