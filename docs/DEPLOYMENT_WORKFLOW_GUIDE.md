# 🚀 GitHub Branch Protection & Deployment Guide

## 📋 Обзор системы

Наш проект теперь использует защищенную модель разработки с двумя основными ветками:

- **DEV** - ветка разработки (автоматические деплои)
- **main** - продакшн ветка (деплои только через PR)

## 🔄 Workflow разработки

### 1. Разработка в DEV ветке
```bash
# Переключиться на DEV ветку
git checkout DEV

# Получить последние изменения
git pull origin DEV

# Создать feature ветку (опционально)
git checkout -b feature/new-feature

# Внести изменения и закоммитить
git add .
git commit -m "feat: add new feature"

# Отправить изменения в DEV
git push origin DEV
```

**Результат:** Автоматический деплой в development environment

### 2. Деплой в продакшн через PR

```bash
# Убедиться что все изменения в DEV
git checkout DEV
git pull origin DEV

# Создать pull request из DEV в main
# Через GitHub UI или CLI:
gh pr create --base main --head DEV --title "Release: New features" --body "Описание изменений"
```

**Процесс:**
1. ✅ Автоматическая валидация PR
2. ✅ Требуется review и approval
3. ✅ После merge - автоматический деплой в продакшн

## 🛡️ Защита веток

### main ветка защищена:
- ❌ Прямые push запрещены
- ✅ Только через pull request
- ✅ Требуется минимум 1 approval
- ✅ Требуется прохождение всех проверок
- ✅ Требуется подписанные коммиты

### DEV ветка открыта:
- ✅ Прямые push разрешены
- ✅ Автоматические деплои
- ✅ Быстрая разработка

## 📁 Структура GitHub Actions

### `.github/workflows/`

1. **auto-deploy.yml** - Продакшн деплой
   - Срабатывает: push в main, merge PR в main
   - Деплоит: Render Production

2. **deploy-dev.yml** - Дев деплой  
   - Срабатывает: push в DEV
   - Деплоит: Render Development

3. **pr-validation.yml** - Валидация PR
   - Срабатывает: создание/обновление PR в main
   - Проверяет: код, тесты, требования

4. **release.yml** - Создание релизов
   - Срабатывает: создание тегов версий

## 🔧 Настройка для разработчиков

### Первоначальная настройка:
```bash
# Клонировать репозиторий
git clone https://github.com/prostoroman/shans-ai.git
cd shans-ai

# Переключиться на DEV ветку
git checkout DEV

# Настроить upstream
git remote add upstream https://github.com/prostoroman/shans-ai.git
```

### Ежедневная работа:
```bash
# Получить последние изменения
git pull origin DEV

# Внести изменения
# ... работа с кодом ...

# Закоммитить и отправить
git add .
git commit -m "feat: описание изменений"
git push origin DEV
```

### Релиз в продакшн:
```bash
# Создать PR через GitHub UI
# Или через CLI:
gh pr create --base main --head DEV --title "Release: $(date +%Y-%m-%d)" --body "Production release"
```

## 🚨 Troubleshooting

### Проблема: "Push rejected - branch is protected"
**Решение:** Используйте pull request вместо прямого push в main

### Проблема: "PR requires review"
**Решение:** Попросите коллегу сделать review или используйте GitHub CLI для self-review (если разрешено)

### Проблема: "Status checks failed"
**Решение:** Исправьте ошибки в коде и обновите PR

### Проблема: "Unsigned commits"
**Решение:** Настройте GPG подпись коммитов:
```bash
git config --global user.signingkey YOUR_GPG_KEY
git config --global commit.gpgsign true
```

## 📊 Мониторинг деплоев

### Проверка статуса:
- **GitHub Actions:** https://github.com/prostoroman/shans-ai/actions
- **Render Dashboard:** Проверьте статус сервисов в Render

### Уведомления:
- GitHub отправляет уведомления о статусе деплоев
- Проверяйте логи в GitHub Actions для деталей

## 🎯 Best Practices

1. **Всегда работайте в DEV ветке**
2. **Создавайте осмысленные commit messages**
3. **Пишите подробные описания PR**
4. **Тестируйте изменения перед созданием PR**
5. **Регулярно синхронизируйтесь с DEV веткой**
6. **Используйте semantic versioning для релизов**

## 📞 Поддержка

При возникновении проблем:
1. Проверьте этот документ
2. Посмотрите логи в GitHub Actions
3. Обратитесь к администратору репозитория
