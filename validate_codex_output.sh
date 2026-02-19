#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Validando código gerado pelo Codex..."

echo "📦 Build..."
npm run build

echo "🧪 Testes..."
npm test -- --coverage --threshold=80

echo "✨ Lint..."
npm run lint

echo "📘 Type check..."
npm run type-check

echo "🔒 Security audit..."
npm audit --audit-level=high

echo "✅ Validação completa!"
