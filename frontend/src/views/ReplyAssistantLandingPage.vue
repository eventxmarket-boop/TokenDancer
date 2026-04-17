<script setup lang="ts">
import { ref } from 'vue'

const selectedSticker = ref<'reply' | 'how-to-do'>('reply')

function activateSticker(sticker: 'reply' | 'how-to-do') {
  selectedSticker.value = sticker
}
</script>

<template>
  <section class="home-landing">
    <div class="home-landing__body">
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
            :class="{ 'home-sticker--active': selectedSticker === 'reply', 'home-sticker--inactive': selectedSticker === 'how-to-do' }"
          >
            <span class="home-sticker__tag">我该怎么回</span>
            <h2>我该怎么回</h2>
            <p>回消息。</p>
          </article>
        </RouterLink>

        <RouterLink
          class="home-sticker-link"
          to="/how-to-do"
          aria-label="我该怎么做"
          @mouseenter="activateSticker('how-to-do')"
          @focus="activateSticker('how-to-do')"
          @click="activateSticker('how-to-do')"
        >
          <article
            class="home-sticker home-sticker--seed"
            :class="{ 'home-sticker--active': selectedSticker === 'how-to-do', 'home-sticker--inactive': selectedSticker === 'reply' }"
          >
            <span class="home-sticker__tag">我该怎么做</span>
            <h2>我该怎么做</h2>
            <p>做事情。</p>
          </article>
        </RouterLink>
      </div>

      <div class="home-actions">
        <RouterLink class="primary-btn" to="/reply-assistant/workbench">我该怎么回</RouterLink>
        <RouterLink class="secondary-btn" to="/how-to-do">我该怎么做</RouterLink>
      </div>
    </div>
  </section>
</template>
