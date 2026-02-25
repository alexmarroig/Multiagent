#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Validando código gerado pelo Codex..."

run_step() {
  local label="$1"
  shift
  echo "$label"
  "$@"
}

if [ -f "pnpm-workspace.yaml" ] || [ -f "pnpm-lock.yaml" ]; then
  PM="pnpm"
  INSTALL_CMD=(pnpm install --frozen-lockfile)
  BUILD_CMD=(pnpm -r --if-present build)
  TEST_CMD=(pnpm -r --if-present test)
  LINT_CMD=(pnpm -r --if-present lint)
  TYPE_CMD=(pnpm -r --if-present type-check)
  AUDIT_CMD=(pnpm audit --audit-level high)
elif [ -f "package.json" ]; then
  PM="npm"
  INSTALL_CMD=(npm ci)
  BUILD_CMD=(npm run build)
  TEST_CMD=(npm test -- --coverage --threshold=80)
  LINT_CMD=(npm run lint)
  TYPE_CMD=(npm run type-check)
  AUDIT_CMD=(npm audit --audit-level=high)
else
  echo "❌ Nenhum gerenciador suportado identificado (npm/pnpm)."
  exit 1
fi

echo "📦 Gerenciador detectado: $PM"

run_step "📥 Instalando dependências..." "${INSTALL_CMD[@]}"
run_step "🏗️ Build..." "${BUILD_CMD[@]}"
run_step "🧪 Testes..." "${TEST_CMD[@]}"
run_step "✨ Lint..." "${LINT_CMD[@]}"
run_step "📘 Type check..." "${TYPE_CMD[@]}"
run_step "🔒 Security audit..." "${AUDIT_CMD[@]}" || echo "⚠️ Audit failed, but continuing..."

echo "✅ Validação completa!"
