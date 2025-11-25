#!/bin/bash

# 电商自动化测试系统 - 一键启动脚本

set -e

echo "======================================"
echo "  电商自动化测试系统"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3${NC}"
    exit 1
fi

# 检查并安装依赖
echo -e "${YELLOW}[1/4] 检查依赖...${NC}"
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "安装依赖包..."
pip install -q fastapi uvicorn pytest requests pydantic PyYAML pytest-html

# 启动 FastAPI 服务
echo -e "${YELLOW}[2/4] 启动 FastAPI 服务...${NC}"
python3 api/ecommerce_api.py &
API_PID=$!
echo "API 服务 PID: $API_PID"

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务是否启动成功
if curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✓ API 服务启动成功${NC}"
else
    echo -e "${RED}✗ API 服务启动失败${NC}"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# 运行测试
echo -e "${YELLOW}[3/4] 运行自动化测试...${NC}"
pytest tests/ -v --tb=short --cov=api --cov=utils -cov=models --html=report.html --self-contained-html

TEST_EXIT_CODE=$?

# 停止 API 服务
echo -e "${YELLOW}[4/4] 清理资源...${NC}"
kill $API_PID 2>/dev/null || true
echo "API 服务已停止"

# 显示测试结果
echo ""
echo "======================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过!${NC}"
else
    echo -e "${RED}✗ 部分测试失败${NC}"
fi
echo "======================================"
echo ""
echo "测试报告: report.html"
echo ""

exit $TEST_EXIT_CODE