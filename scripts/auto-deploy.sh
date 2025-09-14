#!/bin/bash

# Скрипт автоматического развертывания
# Выполняет коммит изменений и push в main ветку

echo "🚀 Starting auto-deploy process..."

# Проверяем статус git
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
    exit 0
fi

# Добавляем все изменения
echo "📝 Adding all changes..."
git add .

# Создаем коммит с временной меткой
COMMIT_MESSAGE="Feature: Enhanced /portfolio command - support for tickers only and percentage weights $(date '+%Y-%m-%d %H:%M:%S')"
echo "💾 Committing changes: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

# Push в main ветку
echo "🚀 Pushing to main branch..."
git push origin main

echo "✅ Auto-deploy completed successfully!"
echo "🔄 GitHub Actions will now deploy to Render automatically"
