#!/bin/bash

# Скрипт автоматического развертывания для Production
# Выполняет коммит изменений и push в main ветку для развертывания в production

echo "🚀 Starting PRODUCTION auto-deploy process..."

# Проверяем статус git
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
    exit 0
fi

# Добавляем все изменения
echo "📝 Adding all changes..."
git add .

# Создаем коммит с временной меткой
COMMIT_MESSAGE="PROD: Auto-deploy $(date '+%Y-%m-%d %H:%M:%S')"
echo "💾 Committing changes: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

# Push в main ветку
echo "🚀 Pushing to main branch..."
git push origin main

echo "✅ PRODUCTION auto-deploy completed successfully!"
echo "🔄 GitHub Actions will now deploy to Render Production automatically"
