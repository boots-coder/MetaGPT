#!/bin/bash
# WMDT 快速测试脚本

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      WMDT Quick Test Script                              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查是否在 wmdt 环境
if [[ "$CONDA_DEFAULT_ENV" != "wmdt" ]]; then
    echo "⚠️  请先激活 wmdt 环境："
    echo "   conda activate wmdt"
    exit 1
fi

# 检查是否在正确的目录
if [[ ! -f "wmdt/__init__.py" ]]; then
    echo "⚠️  请在 MetaGPT 根目录下运行此脚本"
    exit 1
fi

echo "📦 环境检查通过"
echo ""

# 运行基础测试
echo "🧪 运行基础测试..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python -m wmdt.tests.test_basic_workflow

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 基础测试通过！"
    echo ""
    echo "下一步："
    echo "  运行完整实验: python -m wmdt.experiments.run_experiment"
else
    echo ""
    echo "❌ 测试失败，请检查错误信息"
fi
