    交互逻辑说明：
常态：球体安静悬浮，波纹不可见
hover：球体微膨胀，波纹开始"呼吸"——缓慢地放大缩小，像心跳，表示"我在听"
click：波纹瞬间炸开扩散，球体微缩回弹，给用户"被激活"的物理反馈
波纹层用 pointer-events: none 确保不干扰球体的点击事件。两层动画独立运行，不会互相打架。


```html
<div class="siri-glob-container">
  <div class="siri-glob-ripple"></div>
  <div class="siri-glob"></div>
</div>
···


```css
 /* ===== Siri-style Glob Component ===== */

.siri-glob-container {
  position: relative;
  width: var(--glob-size, 120px);
  height: var(--glob-size, 120px);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* --- 波纹层 --- */
.siri-glob-ripple {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid var(--glob-color-ripple, rgba(100, 160, 255, 0.3));
  opacity: 0;
  transform: scale(1);
  pointer-events: none;
}

/* --- 球体本体 --- */
.siri-glob {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(
    circle at 35% 35%,
    var(--glob-color-highlight, rgba(160, 200, 255, 0.9)),
    var(--glob-color-mid, rgba(80, 120, 255, 0.6)) 50%,
    var(--glob-color-deep, rgba(40, 60, 180, 0.3)) 100%
  );
  position: relative;
  z-index: 2;
  cursor: pointer;
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94),
              box-shadow 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  box-shadow:
    inset 0 -4px 12px rgba(255, 255, 255, 0.25),
    0 4px 8px rgba(60, 100, 220, 0.2),
    0 12px 40px rgba(80, 130, 255, 0.15);
}

/* --- Hover --- */
.siri-glob-container:hover .siri-glob {
  transform: scale(1.06);
  box-shadow:
    inset 0 -6px 16px rgba(255, 255, 255, 0.35),
    0 6px 12px rgba(60, 100, 220, 0.3),
    0 16px 60px rgba(80, 130, 255, 0.25),
    0 0 80px rgba(100, 160, 255, 0.1);
}

.siri-glob-container:hover .siri-glob-ripple {
  animation: siri-ripple-breathe 2s ease-in-out infinite;
}

/* --- Active --- */
.siri-glob-container:active .siri-glob {
  transform: scale(0.97);
  transition-duration: 0.1s;
}

.siri-glob-container:active .siri-glob-ripple {
  animation: siri-ripple-burst 0.6s ease-out forwards;
}

/* --- 波纹呼吸 --- */
@keyframes siri-ripple-breathe {
  0%   { transform: scale(1);    opacity: 0.4; }
  50%  { transform: scale(1.15); opacity: 0.15; }
  100% { transform: scale(1);    opacity: 0.4; }
}

/* --- 波纹炸开 --- */
@keyframes siri-ripple-burst {
  0%   { transform: scale(1);   opacity: 0.6; }
  100% { transform: scale(1.8); opacity: 0; }
}
```