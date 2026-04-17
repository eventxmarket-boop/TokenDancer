<script setup lang="ts">
import { ref } from 'vue'

const selectedSticker = ref<'create' | 'seed'>('create')

function activateSticker(sticker: 'create' | 'seed') {
  selectedSticker.value = sticker
}
</script>

<template>
  <section class="home-landing">
    <div class="home-landing__body">
      <div class="home-sticker-stack home-sticker-stack--compact">
        <RouterLink
          class="home-sticker-link"
          to="/create"
          aria-label="创建 Seed"
          @mouseenter="activateSticker('create')"
          @focus="activateSticker('create')"
          @click="activateSticker('create')"
        >
          <article
            class="home-sticker home-sticker--create"
            :class="{ 'home-sticker--active': selectedSticker === 'create', 'home-sticker--inactive': selectedSticker === 'seed' }"
          >
            <span class="home-sticker__tag">Create</span>
            <h2>创建 Seed</h2>
            <p>创建。</p>
          </article>
        </RouterLink>

        <RouterLink
          class="home-sticker-link"
          to="/seed"
          aria-label="选择 Seed"
          @mouseenter="activateSticker('seed')"
          @focus="activateSticker('seed')"
          @click="activateSticker('seed')"
        >
          <article
            class="home-sticker home-sticker--seed"
            :class="{ 'home-sticker--active': selectedSticker === 'seed', 'home-sticker--inactive': selectedSticker === 'create' }"
          >
            <span class="home-sticker__tag">Seed</span>
            <h2>选择 Seed</h2>
            <p>开始对话。</p>
          </article>
        </RouterLink>
      </div>

      <div class="home-actions">
        <RouterLink class="primary-btn" to="/create">创建</RouterLink>
        <RouterLink class="secondary-btn" to="/seed">Seed</RouterLink>
      </div>
    </div>
  </section>
</template>
