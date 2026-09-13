# CHORA 主页 Apple 化增强方案

## 诊断：为什么现在"还没有苹果味儿"

我看了主页的当前状态，"苹果味儿"缺的不是某一个大元素，而是**细节的密度**——Apple 的设计感藏在 0.1px 的间距、0.02s 的延迟、0.5 的透明度里。具体来说：

### 缺的 6 件事

| 序号 | 缺什么 | 现在的状态 | Apple 应该是什么样 |
|------|--------|-----------|-------------------|
| 1 | **字体层级不够狠** | 标题和正文的字号差距偏小，缺乏"一眼震撼"的 hero 区域 | Apple 的标题大到压迫，正文小到克制，对比产生戏剧性 |
| 2 | **间距太紧** | 章节之间、段落之间的呼吸感不足，内容挤在一起 | Apple 的页面有大量留白，内容像展品一样被"供"在空间里 |
| 3 | **过渡太硬** | hover/点击没有缓动曲线，或者用的 linear/ease | Apple 全页用 cubic-bezier 做缓动，每个交互都有物理惯性 |
| 4 | **缺少背景层次** | 纯白/纯黑背景，没有深度 | Apple 用极淡的 mesh gradient 做环境光，让页面有"空气感" |
| 5 | **滚动是瞬移** | 没有滚动入场动画，元素突然出现 | Apple 的元素随滚动 fade-up，像电影镜头推移 |
| 6 | **表格像 Excel** | 原生表格样式，边框硬 | Apple 的表格有微妙的 hover 高亮、紧凑的间距 |

---

## 交付文件说明

### 1. CHORA_Apple_Style_Enhancement.css

完整的 Apple-style CSS 增强包，包含：

- **CSS 变量系统**：Apple 调色板（品牌蓝 #0071E3、中性灰阶、玻璃拟态色）
- **排版层级**：clamp() 流体字号，从手机到 4K 屏自动适配
- **玻璃拟态导航栏**：backdrop-filter blur + saturate，滚动后收紧
- **Apple Card 组件**：圆角 18px、微妙阴影、hover 上浮 2px
- **Apple 按钮**：圆角全圆、hover 缩放 1.02 + 蓝色光晕阴影
- **Apple 表格**：紧凑间距、hover 行高亮、表头大写缩略
- **Siri Glob 增强**：内发光 + 接触阴影 + 弥散光晕 + 表面高光 + 波纹呼吸
- **Mesh Gradient 背景**：三层径向渐变叠加，极淡的环境光
- **滚动入场动画**：IntersectionObserver 实现 fade-up，带延迟交错
- **暗色模式**：prefers-color-scheme: dark 完整适配
- **响应式断点**：
  - 手机竖屏 (<480px)：字号缩小、间距压缩、卡片全宽
  - 手机横屏/小平板 (481-768px)：中等适配
  - iPad/平板 (769-1024px)：居中容器 768px
  - 桌面 (>1024px)：容器 980px
  - 大屏桌面 (>1440px)：容器 1120px、字号更大
  - 超大屏 (>2560px)：容器 1400px、基础字号 20px
- **无障碍**：prefers-reduced-motion 禁用动画、打印样式优化

### 2. CHORA_Apple_Style_Enhancement.js

交互增强脚本，包含：

- **滚动入场动画**：IntersectionObserver 监听 .animate-on-scroll 元素，进入视口后添加 .is-visible 类触发 fade-up
- **导航栏滚动效果**：滚动超过 50px 自动添加 .scrolled 类（收紧 + 阴影）
- **平滑锚点滚动**：带导航栏高度偏移补偿的平滑滚动
- **表格横向滚动**：移动端自动包裹表格在可滚动容器中
- **按钮涟漪效果**：点击时白色涟漪从点击位置扩散

### 3. 使用方法

在主页 HTML 的 <head> 中引入 CSS：

```html
<link rel="stylesheet" href="CHORA_Apple_Style_Enhancement.css">
```

在 </body> 前引入 JS：

```html
<script src="CHORA_Apple_Style_Enhancement.js"></script>
```

如果需要背景渐变，在 body 内最前面加：

```html
<div class="mesh-gradient-bg"></div>
```

如果需要滚动动画，给元素加类名：

```html
<section class="animate-on-scroll">...</section>
```

如果需要玻璃拟态导航栏，给导航容器加类名：

```html
<nav class="nav-glass">...</nav>
```

---

## 不同屏幕效果预览说明

### 桌面端 (>=1440px)
- 标题最大 6rem（约 96px），极具视觉冲击
- 容器宽度 1120px，内容居中
- 章节间距 128px，呼吸感充足
- 正文 1.25rem，阅读舒适

### 平板端 (769-1024px)
- 标题 4rem，容器 768px
- 表格自动启用横向滚动（触摸滑动）
- 章节间距 64px

### 手机端竖屏 (<480px)
- 标题最小 1.75rem，保持可读性
- 容器全宽，左右 padding 16px
- 章节间距压缩到 40-64px
- Siri Glob 缩小到 80px
- 表格字号缩小、内边距压缩
- 代码块自动换行

### 暗色模式
- 自动跟随系统偏好
- 背景 #000、卡片 #1C1C1E
- Glob 阴影在暗色下更明显
- Mesh gradient 颜色加深一倍

---

## 核心设计哲学

> Apple 的设计不是"加了什么"，而是"每样东西都刚好在对的位置上"。

这包 CSS/JS 的核心思路：

1. **克制**：不用花哨的装饰，用间距和排版说话
2. **一致**：所有动画用同一套缓动曲线，所有间距用同一套变量
3. **性能**：用 transform/opacity 做动画（GPU 加速），不用 top/left
4. **尊重用户**：prefers-reduced-motion 一键关闭所有动画
5. **渐进增强**：JS 是可选的，CSS 单独也能用；没 JS 页面照样正常显示
