<template>
  <section class="home-landing">
    <div class="home-landing__body">
      <div class="home-landing__copy">
        <p class="eyebrow">人格小屋</p>
        <h1>创造一个人格，也可以直接选择一个人格开始聊天。</h1>
        <p class="hero-text">一个更轻、更直观的入口页。先从自己开始，或者先从一个现成人格开始。</p>
      </div>

      <div class="home-sticker-stack" aria-hidden="true">
        <article class="home-sticker home-sticker--create">
          <span class="home-sticker__tag">Create</span>
          <h2>创建 Seed</h2>
          <p>从自己、资料或关系出发，生成一版人格雏形。</p>
        </article>

        <article class="home-sticker home-sticker--seed">
          <span class="home-sticker__tag">Seed</span>
          <h2>选择 Seed</h2>
          <p>从现成人格里挑一个，直接开始对话。</p>
        </article>
      </div>

      <div class="home-actions">
        <RouterLink class="primary-btn" to="/create">创建 Seed</RouterLink>
        <RouterLink class="secondary-btn" to="/seed">选择 Seed</RouterLink>
      </div>
    </div>
  </section>
</template>
