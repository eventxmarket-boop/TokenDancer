<script setup lang="ts">
const scrollToRoadmap = () => {
  const element = document.getElementById('self-persona-roadmap')
  element?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <section class="hero-card">
    <div class="hero-copy">
      <p class="eyebrow">Create</p>
      <h2>创造一个自我人格。</h2>
      <p class="hero-text">
        这一页先把入口立住：自我人格不是只写一句“我是谁”，而是拆成做事方式和回复方式两层，后面再逐步扩成完整流程。
      </p>
      <div class="hero-actions">
        <button class="primary-btn" type="button" @click="scrollToRoadmap">开始创建</button>
        <RouterLink class="secondary-btn" to="/seed">先去看 Seed</RouterLink>
      </div>
    </div>

    <div class="hero-visual create-visual">
      <div class="floating-orb"></div>
      <div class="spotlight-card">
        <p class="spotlight-card__label">结构提示</p>
        <h3>Work System + Reply Persona</h3>
        <p>先定义做事规则，再定义表达方式。产品后面会围绕这两层继续长出来。</p>
      </div>
    </div>
  </section>

  <section id="self-persona-roadmap" class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">自我人格结构</p>
        <h3>先做两层，再慢慢补细节。</h3>
      </div>
      <p class="section-note">这一版先做入口和说明，不做完整蒸馏流水线。</p>
    </div>

    <div class="create-grid">
      <article class="create-module">
        <div class="create-module__head">
          <p class="eyebrow">Work System</p>
          <h4>做事方式</h4>
        </div>
        <ul class="create-module__list">
          <li>你做决策时先看什么。</li>
          <li>你做事时最稳定的优先级是什么。</li>
          <li>资源有限时你如何取舍。</li>
          <li>你面对不确定性时会怎么推进。</li>
        </ul>
      </article>

      <article class="create-module">
        <div class="create-module__head">
          <p class="eyebrow">Reply Persona</p>
          <h4>回复方式</h4>
        </div>
        <ul class="create-module__list">
          <li>你会先给结论还是先分析。</li>
          <li>你说话更长还是更短。</li>
          <li>你是否常用对比、分点、反问。</li>
          <li>你给建议时会不会强调代价和边界。</li>
        </ul>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">后续步骤</p>
        <h3>未来这页会连接成完整入口。</h3>
      </div>
      <RouterLink class="text-link" to="/favorites">先看收藏人格</RouterLink>
    </div>

    <div class="roadmap-list">
      <article class="roadmap-step">
        <span class="status-pill">1</span>
        <div>
          <h4>写下你的做事规则</h4>
          <p>把你最稳定的判断顺序写成规则，而不是写成空泛口号。</p>
        </div>
      </article>

      <article class="roadmap-step">
        <span class="status-pill">2</span>
        <div>
          <h4>补充你的回复方式</h4>
          <p>明确你说话的节奏、句式、边界和表达偏好。</p>
        </div>
      </article>

      <article class="roadmap-step">
        <span class="status-pill">3</span>
        <div>
          <h4>后面再接完整生成流程</h4>
          <p>等入口和结构稳定后，再把抽取、审核和发布流程接进来。</p>
        </div>
      </article>
    </div>
  </section>
</template>
