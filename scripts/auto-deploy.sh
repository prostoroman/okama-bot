#!/bin/bash

# Скрипт автоматического развертывания для DEV ветки
# Выполняет коммит изменений и push в DEV ветку для развертывания в development

echo "🚀 Starting DEV auto-deploy process..."

# Проверяем статус git
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
    exit 0
fi

# Добавляем все изменения
echo "📝 Adding all changes..."
git add .

# Создаем коммит с временной меткой
COMMIT_MESSAGE="DEV: Auto-deploy $(date '+%Y-%m-%d %H:%M:%S')"
echo "💾 Committing changes: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

# Push в DEV ветку
echo "🚀 Pushing to DEV branch..."
git push origin DEV

echo "✅ DEV auto-deploy completed successfully!"
echo "🔄 GitHub Actions will now deploy to Render Development automatically"
