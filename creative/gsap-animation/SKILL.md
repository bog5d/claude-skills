---
name: gsap-animation
description: GSAP animation for HTML/React — core tweens, timelines, ScrollTrigger, React useGSAP hooks, performance best practices. Use when building animated web pages, scroll-driven effects, React/Next.js animations, or any HTML/CSS animation beyond simple transitions. Pairs with claude-design / guizang-ppt / html-to-video.
version: 1.0.0
tags: [animation, gsap, react, scrolltrigger, html, video]
triggers:
  - animation
  - animate
  - scroll animation
  - gsap
  - scrolltrigger
  - motion
  - parallax
  - timeline animation
related_skills:
  - claude-design
  - guizang-ppt-skill
  - html-to-video
  - taste-anti-slop
---

# GSAP Animation Skill

> 基于 GreenSock 官方 gsap-skills (8 子 skill) 整合。覆盖 core / timeline / ScrollTrigger / React / performance。
> GSAP 是框架无关的动画库，Webflow 的交互引擎就是 GSAP。

---

## 0. 快速决策：用 GSAP 还是 CSS？

| 需求 | 选 GSAP | 选 CSS |
|---|---|---|
| 简单 hover/transition | ❌ | ✅ CSS transition |
| 多步序列动画 | ✅ Timeline | ❌ |
| 运行时控制(暂停/反转/跳转) | ✅ | ❌ |
| 滚动驱动动画 | ✅ ScrollTrigger | ❌ |
| SVG 形变(morphing) | ✅ | ❌ |
| 动态 JS 计算值 | ✅ | ❌ |

GSAP 适用于 **任何框架**：React / Vue / Svelte / Astro / vanilla JS。

---

## 1. Core API — 核心补间

### 基础方法

```javascript
// 引入（CDN 或 npm）
// <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
// npm: npm install gsap

gsap.to(targets, vars)        // 当前值 → vars 值（最常用）
gsap.from(targets, vars)      // vars 值 → 当前值（入场用）
gsap.fromTo(targets, from, to) // 显式起点 → 终点
gsap.set(targets, vars)       // 立即设置（无动画）
```

**属性统一用 camelCase**：`backgroundColor`、`marginTop`、`rotationX`。

### Transform 别名（优先用，不要写原始 transform）

| GSAP | CSS 等价 | 默认单位 |
|---|---|---|
| `x`, `y`, `z` | translateX/Y/Z | px |
| `xPercent`, `yPercent` | translateX/Y % | % |
| `scale`, `scaleX`, `scaleY` | scale | — |
| `rotation` | rotate | deg |
| `rotationX`, `rotationY` | 3D rotate | deg |
| `skewX`, `skewY` | skew | deg |
| `transformOrigin` | transform-origin | — |

```javascript
// ✅ 正确
gsap.to(".box", { x: 100, rotation: 360, scale: 1.2 });
// ❌ 错误
gsap.to(".box", { left: "100px", transform: "rotate(360deg)" });
```

### 常用 vars 参数

```javascript
gsap.to(".box", {
  x: 100,                    // 动画到 x:100
  duration: 1,               // 持续时间(秒)，默认 0.5
  delay: 0.5,                // 延迟(秒)
  ease: "power3.out",        // 缓动曲线，默认 "power1.out"
  stagger: 0.1,              // 批量元素间隔(秒)
  repeat: 2,                 // 重复次数(-1=无限)
  yoyo: true,                // 与 repeat 配合，来回
  autoAlpha: 0,              // opacity + visibility（优于 opacity）
  overwrite: "auto",         // 防止冲突
  onComplete: () => {},      // 完成回调
});
```

### 缓动曲线速查

```javascript
// 从慢到快（常用）
"power1.out"   // 默认
"power2.out"
"power3.out"   // 强烈减速
"power4.out"
// 回弹
"back.out(1.7)"       // overshoot
"elastic.out(1, 0.3)" // 弹力
// 特殊
"none"                // 线性
"bounce.out"
// 完整命名：power1/2/3/4 + .in / .out / .inOut
```

### Stagger 进阶

```javascript
// 基础
gsap.to(".item", { y: -20, stagger: 0.1 });

// 高级对象写法
gsap.to(".item", {
  y: -20,
  stagger: {
    amount: 0.3,       // 总时间
    from: "center",    // "start" | "center" | "end" | "edges" | "random" | index
    ease: "power2.in",
  }
});
```

### 关键技巧

```javascript
// 相对值
gsap.to(".box", { x: "+=20" });  // 在当前位置 +20

// 方向旋转（最短路径）
gsap.to(".box", { rotation: "-170_short" });  // 20° 顺时针，不是 340°
gsap.to(".box", { rotation: "+=30_cw" });    // 顺时针 30°

// 函数值：每个目标调用一次
gsap.to(".item", { x: (i, target, targets) => i * 50 });

// 存储引用控制播放
const tween = gsap.to(".box", { x: 100, duration: 1, repeat: 1, yoyo: true });
tween.pause();
tween.play();
tween.reverse();
tween.kill();
tween.progress(0.5);  // 跳转到 50%
tween.time(0.2);       // 跳转到 0.2s
```

---

## 2. Timeline — 序列编排

```javascript
const tl = gsap.timeline();

tl.to(".a", { x: 100, duration: 1 })
  .to(".b", { y: 50, duration: 0.5 })
  .to(".c", { opacity: 0, duration: 0.3 });
// 默认串联：a 结束 → b 开始 → c 开始
```

### Position Parameter（控制时序的关键）

```javascript
tl.to(".a", { x: 100 }, 0);           // 绝对时间：从 0s 开始
tl.to(".b", { y: 50 }, "+=0.5");      // 上一个结束后 0.5s
tl.to(".c", { opacity: 0 }, "-=0.2"); // 上一个结束前 0.2s（重叠）
tl.to(".d", { scale: 2 }, "<");       // 与上一个同时开始
tl.to(".e", { rotation: 45 }, "<0.2"); // 上一个开始后 0.2s
```

### Labels & Nesting

```javascript
const tl = gsap.timeline({ defaults: { duration: 0.5, ease: "power2.out" } });
tl.addLabel("intro", 0);
tl.to(".a", { x: 100 }, "intro");
tl.addLabel("outro", "+=0.5");
tl.to(".b", { opacity: 0 }, "outro");
tl.play("outro");             // 从 outro 开始播放

// 嵌套 Timeline
const master = gsap.timeline();
const child = gsap.timeline();
child.to(".a", { x: 100 }).to(".b", { y: 50 });
master.add(child, 0);          // 把子 timeline 嵌入
master.to(".c", { opacity: 0 }, "+=0.2");
```

### ⚠️ 铁律

- ✅ 用 Timeline 替代 `delay` 串联
- ✅ 用 `defaults` 统一 duration/ease
- ✅ ScrollTrigger 放 Timeline 上，别放子 tween 里
- ❌ 不要在嵌套的子 tween 上加 ScrollTrigger

---

## 3. ScrollTrigger — 滚动驱动动画

```javascript
// 注册插件
gsap.registerPlugin(ScrollTrigger);

// 基础用法
gsap.to(".box", {
  x: 500,
  scrollTrigger: {
    trigger: ".box",           // 触发器元素
    start: "top center",       // 触发条件：元素顶部到达视口中心
    end: "bottom center",      // 结束条件
    toggleActions: "play reverse play reverse", // 进入/离开/返回进入/返回离开
  }
});
```

### 关键配置

```javascript
scrollTrigger: {
  trigger: ".section",
  start: "top 80%",           // 元素顶部到达视口 80%
  end: "+=500",               // 滚动 500px 后结束
  scrub: true,                // 滚动联动（数字=缓动秒数如 scrub:1）
  pin: true,                  // 固定元素
  pinSpacing: true,           // 自动加占位（默认 true）
  markers: true,              // 开发标记⚠️（生产删掉！）
  once: true,                 // 只触发一次
  toggleClass: { targets: ".nav", className: "scrolled" },
}
```

### start/end 格式

```
"triggerPosition viewportPosition"
"top top"       // 元素顶部碰到视口顶部
"center center" // 元素中心碰到视口中心
"bottom 80%"    // 元素底部到视口 80%
"+=300"         // 滚动 300px
"+=100%"        // 滚动一个视口高度
"max"           // 最大滚动距离
```

### Pinning（固定效果）

```javascript
gsap.to(".inner", { scale: 2, duration: 1,
  scrollTrigger: {
    trigger: ".section",
    start: "top top",
    end: "+=1000",
    pin: true,       // 固定 .section
    scrub: 1,
  }
});
// ⚠️ 不要动画 .section 本身，动画它的子元素
```

### ScrollTrigger.batch() — 批量可见元素

```javascript
ScrollTrigger.batch(".card", {
  interval: 0.1,
  batchMax: 4,
  onEnter: (elements, triggers) => {
    gsap.to(elements, { opacity: 1, y: 0, stagger: 0.1 });
  },
  start: "top 85%",
});
```

### Standalone（无动画的滚动触发）

```javascript
ScrollTrigger.create({
  trigger: "#progress",
  start: "top top",
  end: "bottom bottom",
  onUpdate: (self) => console.log(self.progress.toFixed(3)),
});
```

---

## 4. React / Next.js 集成

```bash
npm install gsap @gsap/react
```

### useGSAP() Hook（推荐，替代 useEffect）

```javascript
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(useGSAP, ScrollTrigger);

function MyComponent() {
  const containerRef = useRef(null);

  useGSAP(() => {
    gsap.to(".box", { x: 100 });
    gsap.from(".item", { opacity: 0, y: 30, stagger: 0.1 });
  }, { scope: containerRef }); // scope 限定选择器范围

  // ...jsx
}
```

### useGSAP 进阶

```javascript
const { contextSafe } = useGSAP(() => {
  // 初始动画
  gsap.from(".item", { opacity: 0, stagger: 0.1 });
}, {
  dependencies: [data],     // 依赖数组（类似 useEffect）
  scope: containerRef,
  revertOnUpdate: true,     // 依赖变化时 revert + 重跑
});

// contextSafe 包装事件回调：组件卸载后自动 no-op
const onClick = contextSafe(() => {
  gsap.to(".box", { rotation: 180 });
});
```

### useEffect 降级写法（不用 @gsap/react 时）

```javascript
useEffect(() => {
  const ctx = gsap.context(() => {
    gsap.to(".box", { x: 100 });
    gsap.from(".item", { opacity: 0, stagger: 0.1 });
  }, containerRef);
  return () => ctx.revert(); // ⚠️ 必须 revert
}, []);
```

### ⚠️ React 铁律

- ✅ 用 useGSAP() 替代 useEffect
- ✅ 用 refs 定位元素，不用字符串选择器（除非有 scope）
- ✅ 事件回调用 `contextSafe` 包裹
- ❌ 忘记 cleanup → 内存泄漏 + 已卸载组件警告
- ❌ SSR 时在 useEffect/useGSAP 外引用 `window`

---

## 5. Performance — 性能铁律

### 只动画 transform + opacity

```javascript
// ✅ 优先（compositor only，不触发 layout/paint）
gsap.to(".box", { x: 100, scale: 1.2, opacity: 0.8 });

// ❌ 避免（触发 layout）
gsap.to(".box", { width: 300, height: 200, top: 100, left: 50, margin: 20 });
```

### 其他性能规则

- ✅ `will-change: transform` 只在动画元素上设置（不要全局加）
- ✅ 用 `stagger` 而非 N 个独立 tween
- ✅ 高频更新（如鼠标跟随）用 `gsap.quickTo()`
- ✅ 不可见/离屏动画 `pause()` 或 `kill()`
- ❌ 不要给每个元素都设 `will-change` 或 `force3D`
- ❌ 不要创建数百个并行的 tween/ScrollTrigger

```javascript
// quickTo 示例：鼠标跟随
const xTo = gsap.quickTo("#pointer", "x", { duration: 0.4, ease: "power3" });
const yTo = gsap.quickTo("#pointer", "y", { duration: 0.4, ease: "power3" });
window.addEventListener("mousemove", e => { xTo(e.pageX); yTo(e.pageY); });
```

---

## 6. 常用模式速查

### 入场动画（hero 加载）

```javascript
const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
tl.from("h1", { y: 40, opacity: 0, duration: 0.8 })
  .from("p", { y: 20, opacity: 0, duration: 0.6 }, "-=0.3")
  .from(".cta", { y: 10, opacity: 0, duration: 0.4 }, "-=0.2");
```

### 滚动揭示（scroll reveal）

```javascript
gsap.utils.toArray(".reveal").forEach(el => {
  gsap.from(el, {
    y: 60, opacity: 0, duration: 1,
    scrollTrigger: { trigger: el, start: "top 85%", once: true }
  });
});
```

### 视差效果

```javascript
gsap.to(".parallax-bg", {
  yPercent: 30,
  ease: "none",
  scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true }
});
```

### 水平滚动画廊

```javascript
const sections = gsap.utils.toArray(".panel");
gsap.to(sections, {
  xPercent: -100 * (sections.length - 1),
  ease: "none",
  scrollTrigger: {
    trigger: ".gallery",
    pin: true,
    scrub: 1,
    end: "+=3000",
  }
});
```

---

## 7. 与 Hermes Skill 配合

| 任务 | 加载顺序 |
|---|---|
| 视频幻灯片 + 动画 | `taste-anti-slop` → `gsap-animation` → `html-to-video` |
| 动画 Landing Page | `taste-anti-slop` → `gsap-animation` → `claude-design` |
| 滚动叙事 PPT | `guizang-ppt-skill` → `gsap-animation` |
| React 项目 | `gsap-animation` + 项目自有 skill |

**规则：gsap-animation 在 taste-anti-slop 之后加载。三刻度盘的 MOTION_INTENSITY 直接映射到动画密度。**
