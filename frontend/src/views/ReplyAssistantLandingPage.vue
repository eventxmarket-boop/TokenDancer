<script setup lang="ts">
import { ref } from 'vue'

const selectedSticker = ref<'reply'>('reply')

function activateSticker(sticker: 'reply') {
  selectedSticker.value = sticker
}
</script>

<template>
  <section class="home-landing">
    <div class="home-landing__body">
      <div class="home-landing__copy">
        <p class="hero-text">先从一句话开始，或者先想清楚要做什么。</p>
      </div>

      <div class="home-sticker-stack home-sticker-stack--compact">
        <RouterLink
          class="home-sticker-link"
          to="/reply-assistant/workbench"
          aria-label="我该怎么回"
          @mouseenter="activateSticker('reply')"
          @focus="activateSticker('reply')"
          @click="activateSticker('reply')"
        >
          <article
            class="home-sticker home-sticker--create"
            :class="{ 'home-sticker--active': selectedSticker === 'reply' }"
          >
            <span class="home-sticker__tag">我该怎么回</span>
            <h2>我该怎么回</h2>
            <p>直接输入一句话，给你能直接发的回复。</p>
          </article>
        </RouterLink>
      </div>

      <div class="home-actions">
        <RouterLink class="primary-btn" to="/reply-assistant/workbench">我该怎么回</RouterLink>
      </div>
    </div>
  </section>
</template>
