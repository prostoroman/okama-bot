# GitHub Branch Protection Setup

## Настройка защиты ветки main

Для настройки защиты ветки main от прямых push и разрешения деплоев только через pull request выполните следующие шаги:

### 1. Перейдите в настройки репозитория
1. Откройте репозиторий `prostoroman/shans-ai` в GitHub
2. Перейдите в **Settings** → **Branches**

### 2. Настройте защиту ветки main
1. Нажмите **Add rule** или **Add branch protection rule**
2. В поле **Branch name pattern** введите: `main`
3. Включите следующие настройки:

#### Обязательные настройки:
- ✅ **Require a pull request before merging**
  - ✅ **Require approvals** (минимум 1)
  - ✅ **Dismiss stale PR approvals when new commits are pushed**
  - ✅ **Require review from code owners** (если есть CODEOWNERS файл)

- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  - Добавьте статус-чеки:
    - `deploy-prod` (из workflow auto-deploy.yml)
    - `test` (если есть тесты)

- ✅ **Require conversation resolution before merging**

- ✅ **Require signed commits**

- ✅ **Require linear history**

- ✅ **Restrict pushes that create files larger than 100 MB**

#### Дополнительные настройки:
- ✅ **Do not allow bypassing the above settings**
- ✅ **Restrict pushes that create files larger than 100 MB**
- ✅ **Require deployments to succeed before merging**

### 3. Настройка администраторов
- ✅ **Include administrators** (применить правила и к администраторам)

### 4. Сохранение настроек
- Нажмите **Create** или **Save changes**

## Результат

После настройки:
- ❌ **Прямые push в main будут запрещены**
- ✅ **Деплои в main возможны только через pull request**
- ✅ **Деплои в DEV остаются автоматическими при push**
- ✅ **Все изменения в main требуют review и approval**

## Workflow файлы

### auto-deploy.yml (Production)
- Срабатывает только при push в `main`
- Требует pull request для срабатывания
- Деплоит в production на Render

### deploy-dev.yml (Development)  
- Срабатывает при push в `DEV`
- Автоматический деплой без ограничений
- Деплоит в development на Render

### release.yml
- Срабатывает при создании тегов версий
- Создает релизы в GitHub

## Проверка настроек

После настройки проверьте:
1. Попробуйте сделать прямой push в main - должно быть запрещено
2. Создайте pull request из DEV в main - должен требовать approval
3. Push в DEV должен автоматически деплоить в development
4. Merge pull request в main должен деплоить в production

## Troubleshooting

Если возникают проблемы:
1. Проверьте права доступа к репозиторию
2. Убедитесь, что все необходимые статус-чеки настроены
3. Проверьте, что все участники имеют необходимые права
4. Убедитесь, что GitHub Actions включены в настройках репозитория
