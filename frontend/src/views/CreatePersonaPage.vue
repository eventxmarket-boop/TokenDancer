<script setup lang="ts">
const scrollToRoadmap = () => {
  const element = document.getElementById('self-persona-roadmap')
  element?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <section class="page-hero">
    <div class="hero-copy">
      <p class="eyebrow">Create</p>
      <h1>用你的材料，创造一个更像你的自我人格。</h1>
      <p class="hero-text">
        这一页是自我人格的入口，不是简单的说明页。先把你如何做事、如何表达、如何给建议这三件事讲清楚，后面再逐步接入完整蒸馏流程。
      </p>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>2</strong><span>核心层</span></span>
        <span class="metric-chip"><strong>5</strong><span>支持材料类型</span></span>
        <span class="metric-chip"><strong>1</strong><span>入口页</span></span>
      </div>

      <div class="hero-actions">
        <button class="primary-btn" type="button" @click="scrollToRoadmap">开始创建</button>
        <RouterLink class="secondary-btn" to="/seed">先去看 Seed</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">Work System</p>
        <h3 class="hero-band__title">做事方式</h3>
        <p class="hero-band__copy">先定义你的判断顺序、优先级和取舍方式，这是人格的“行动系统”。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">Reply Persona</p>
        <h3 class="hero-band__title">回复方式</h3>
        <p class="hero-band__copy">再定义你的表达节奏、句式偏好和边界，这是人格的“表达层”。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">下一步</p>
        <h3 class="hero-band__title">上传资料后再蒸馏</h3>
        <p class="hero-band__copy">聊天记录、PDF、音频、视频和数字痕迹都可以作为后续扩展输入。</p>
      </article>
    </div>
  </section>

  <section id="self-persona-roadmap" class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">Create Roadmap</p>
        <h3>先做产品入口，再逐步接完整生成流程。</h3>
      </div>
      <p class="section-note">这一步重点是把产品讲清楚，而不是先把后端训练链路做重。</p>
    </div>

    <div class="create-grid create-grid--three">
      <article class="create-module">
        <div class="create-module__head">
          <p class="eyebrow">01</p>
          <h4>自我人格</h4>
        </div>
        <p class="state-copy">先把你自己的做事方式与回复方式整理成两个核心模块。</p>
        <ul class="create-module__list">
          <li>做决策时先看什么</li>
          <li>遇到资源有限怎么取舍</li>
          <li>表达时更偏结论还是分析</li>
        </ul>
      </article>

      <article class="create-module">
        <div class="create-module__head">
          <p class="eyebrow">02</p>
          <h4>上传资料生成</h4>
        </div>
        <p class="state-copy">后续可以接聊天记录、文档、PDF、音频和视频等材料作为蒸馏输入。</p>
        <ul class="create-module__list">
          <li>聊天记录</li>
          <li>PDF / 文档</li>
          <li>音频 / 视频</li>
        </ul>
      </article>

      <article class="create-module">
        <div class="create-module__head">
          <p class="eyebrow">03</p>
          <h4>数字分身</h4>
        </div>
        <p class="state-copy">更高保真的方向可以继续保留为后续增强，而不是首发主线。</p>
        <ul class="create-module__list">
          <li>更长上下文</li>
          <li>更完整蒸馏链路</li>
          <li>后续训练 / 部署</li>
        </ul>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">支持材料</p>
        <h3>这页先把用户可以提供什么说透。</h3>
      </div>
      <RouterLink class="text-link" to="/favorites">先看收藏人格</RouterLink>
    </div>

    <div class="feature-grid feature-grid--three">
      <article class="feature-card">
        <p class="feature-card__label">文本</p>
        <h4>聊天记录 / 文章 / 笔记</h4>
        <p>适合提炼表达习惯、决策模式和常用观点。</p>
      </article>

      <article class="feature-card">
        <p class="feature-card__label">文件</p>
        <h4>PDF / 文档 / 资料包</h4>
        <p>适合抽取结构化内容、主题脉络和长期重复的判断框架。</p>
      </article>

      <article class="feature-card">
        <p class="feature-card__label">多媒体</p>
        <h4>音频 / 视频 / 数字痕迹</h4>
        <p>适合后续扩展更高保真的自我人格输入方式。</p>
      </article>
    </div>
  </section>
</template>
