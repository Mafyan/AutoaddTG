# 🎨 ДИЗАЙН-СИСТЕМА USER CONTROL BOT 2025

## 📋 Обзор

Современная, доступная и темизируемая дизайн-система построенная на CSS переменных с полной поддержкой Dark/Light режимов.

---

## 🎨 ЦВЕТОВАЯ ПАЛИТРА

### Brand Colors
```css
--brand-primary: #6366f1      /* Основной фиолетовый */
--brand-primary-hover: #4f46e5
--brand-primary-active: #4338ca
--brand-secondary: #8b5cf6    /* Вторичный */
--brand-accent: #ec4899        /* Акцент (розовый) */
```

### Semantic Colors
- **Success:** `#10b981` (зелёный) - успешные действия
- **Warning:** `#f59e0b` (оранжевый) - предупреждения
- **Error:** `#ef4444` (красный) - ошибки
- **Info:** `#3b82f6` (синий) - информация

### Neutral Palette (адаптируется к теме)
```
50  → 900 (от светлого к тёмному в light theme)
900 → 50 (инвертируется в dark theme)
```

---

## 📏 SPACING SYSTEM

Используем 8-пиксельную сетку:

```css
--space-1: 4px    --space-8: 32px
--space-2: 8px    --space-10: 40px
--space-3: 12px   --space-12: 48px
--space-4: 16px   --space-16: 64px
--space-5: 20px   --space-20: 80px
--space-6: 24px   --space-24: 96px
```

---

## ✍️ ТИПОГРАФИКА

### Font Stack
```css
-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
'Helvetica Neue', Arial, sans-serif
```

### Размеры шрифтов
```css
--text-xs: 12px    --text-2xl: 24px
--text-sm: 14px    --text-3xl: 30px
--text-base: 16px  --text-4xl: 36px
--text-lg: 18px    --text-5xl: 48px
--text-xl: 20px    --text-6xl: 60px
```

### Font Weights
```css
--font-light: 300
--font-normal: 400
--font-medium: 500
--font-semibold: 600
--font-bold: 700
--font-extrabold: 800
```

### Line Heights
```css
--leading-none: 1
--leading-tight: 1.25
--leading-normal: 1.5
--leading-loose: 2
```

---

## 🔲 BORDER RADIUS

```css
--radius-sm: 6px     /* Мелкие элементы */
--radius-md: 8px     /* Кнопки, инпуты */
--radius-lg: 12px    /* Карточки */
--radius-xl: 16px    /* Модалы */
--radius-2xl: 24px   /* Крупные модалы */
--radius-full: 9999px /* Круглые элементы */
```

---

## 🌗 ТЕМЫ

### Light Theme (по умолчанию)
- **Background:** `#ffffff`
- **Text Primary:** `#171717`
- **Surface:** Белый с тенями

### Dark Theme
- **Background:** `#0a0a0a`
- **Text Primary:** `#f5f5f5`
- **Surface:** `#171717` с приподнятыми элементами

### Переключение темы
```javascript
// Автоматическое определение системной темы
// Сохранение выбора в localStorage
// Плавные переходы между темами
```

---

## 🎭 SHADOWS

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1)
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25)
```

---

## 🧩 КОМПОНЕНТЫ

### Кнопки
```html
<!-- Варианты -->
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-outline">Outline</button>
<button class="btn btn-ghost">Ghost</button>

<!-- Размеры -->
<button class="btn btn-sm">Small</button>
<button class="btn">Default</button>
<button class="btn btn-lg">Large</button>

<!-- Состояния -->
<button class="btn" disabled>Disabled</button>
<button class="btn btn-loading">Loading</button>
```

### Карточки
```html
<div class="card card-hover">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
    <p class="card-description">Description</p>
  </div>
  <div class="card-body">
    Content
  </div>
  <div class="card-footer">
    <button class="btn btn-primary">Action</button>
  </div>
</div>
```

### Stat Cards
```html
<div class="stat-card">
  <div class="stat-card-icon" style="background: #e3f2fd; color: #1976d2;">
    <i class="bi bi-people"></i>
  </div>
  <div class="stat-card-value">1,234</div>
  <div class="stat-card-label">Total Users</div>
</div>
```

### Badges
```html
<span class="badge badge-success">Success</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-error">Error</span>
<span class="badge badge-info">Info</span>
```

### Forms
```html
<div class="form-group">
  <label class="form-label form-label-required">Name</label>
  <input type="text" class="form-control" placeholder="Enter name">
  <span class="form-helper">Helper text</span>
  <span class="form-error">Error message</span>
</div>
```

### Toasts
```javascript
showToast('Message', 'success'); // or 'error', 'warning', 'info'
```

---

## ⚡ TRANSITIONS

```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1)
--transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1)
--transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1)
--transition-bounce: 500ms cubic-bezier(0.68, -0.55, 0.265, 1.55)
```

---

## ♿ ДОСТУПНОСТЬ

### Focus States
- Visible focus rings (`outline` + `box-shadow`)
- Keyboard navigation полностью поддерживается
- ARIA labels на всех интерактивных элементах

### Контрастность
- Минимум WCAG AA (4.5:1 для текста)
- WCAG AAA для важных элементов (7:1)

### Motion
- Респект к `prefers-reduced-motion`
- Отключение анимаций для пользователей с чувствительностью

### Screen Readers
- Semantic HTML
- ARIA roles и labels
- Skip links для навигации

---

## 📱 RESPONSIVE BREAKPOINTS

```css
/* Mobile First подход */
< 576px: Mobile (small)
< 768px: Mobile (large)
< 992px: Tablet
< 1200px: Desktop (small)
≥ 1200px: Desktop (large)
```

---

## 🚀 ИСПОЛЬЗОВАНИЕ

### Подключение
```html
<link rel="stylesheet" href="/static/css/design-system.css">
<link rel="stylesheet" href="/static/css/components.css">
<link rel="stylesheet" href="/static/css/layout.css">
```

### Быстрый старт
```html
<div class="main-content">
  <div class="page-header">
    <h1 class="page-title">Page Title</h1>
    <div class="page-actions">
      <button class="btn btn-primary">Action</button>
    </div>
  </div>
  
  <div class="grid-4">
    <!-- Stat cards or content -->
  </div>
</div>
```

---

## 📦 ФАЙЛОВАЯ СТРУКТУРА

```
static/css/
├── design-system.css  # Переменные, цвета, типографика, базовые стили
├── components.css     # Переиспользуемые компоненты
└── layout.css         # Layout (sidebar, main content, grid)
```

---

## 🎯 BEST PRACTICES

1. **Используйте CSS переменные** вместо hardcoded значений
2. **Mobile-first** подход к адаптивности
3. **Semantic HTML** для SEO и доступности
4. **Не используйте `!important`** без крайней необходимости
5. **Тестируйте в Dark mode** всё что создаёте
6. **Keyboard navigation** должна работать везде
7. **Loading states** для асинхронных действий
8. **Empty states** когда нет данных

---

## 🔧 КАСТОМИЗАЦИЯ

Можно переопределить любые CSS переменные:

```css
:root {
  --brand-primary: #your-color;
  --sidebar-width: 320px;
}
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- **Bootstrap Icons:** https://icons.getbootstrap.com/
- **Bootstrap Grid:** Используется для адаптивности
- **WCAG Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/

---

**Создано:** 2025  
**Версия:** 1.0.0  
**Лицензия:** Internal Use

