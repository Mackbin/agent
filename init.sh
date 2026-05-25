#!/bin/bash

# AI Gateway 初始化脚本

set -e

echo "========================================"
echo "AI Gateway 初始化脚本"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "${YELLOW}检查 Python 版本...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本：$python_version"

# 创建虚拟环境
echo -e "${YELLOW}创建虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
else
    echo -e "${YELLOW}⚠ 虚拟环境已存在${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

# 安装依赖
echo -e "${YELLOW}安装 Python 依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 检查 Docker
echo -e "${YELLOW}检查 Docker...${NC}"
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo "Docker: $docker_version"
else
    echo -e "${RED}✗ Docker 未安装，请手动安装 Docker${NC}"
fi

# 检查 Docker Compose
echo -e "${YELLOW}检查 Docker Compose...${NC}"
if command -v docker-compose &> /dev/null; then
    compose_version=$(docker-compose --version)
    echo "Docker Compose: $compose_version"
else
    echo -e "${RED}✗ Docker Compose 未安装${NC}"
fi

# 创建日志目录
echo -e "${YELLOW}创建日志目录...${NC}"
mkdir -p logs
echo -e "${GREEN}✓ 日志目录创建成功${NC}"

# 创建 SSL 目录
echo -e "${YELLOW}创建 SSL 目录...${NC}"
mkdir -p ssl
echo -e "${GREEN}✓ SSL 目录创建成功${NC}"

# 复制环境配置文件
echo -e "${YELLOW}配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env 文件创建成功，请编辑配置${NC}"
else
    echo -e "${YELLOW}⚠ .env 文件已存在${NC}"
fi

# 初始化数据库（如果使用 Docker）
if command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}是否启动 Docker 服务？(y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${YELLOW}启动 Docker 服务...${NC}"
        docker-compose up -d db redis
        echo -e "${GREEN}✓ 数据库和 Redis 已启动${NC}"
        
        # 等待数据库就绪
        echo -e "${YELLOW}等待数据库就绪...${NC}"
        sleep 5
        
        # 运行数据库迁移
        echo -e "${YELLOW}运行数据库迁移...${NC}"
        alembic upgrade head
        echo -e "${GREEN}✓ 数据库迁移完成${NC}"
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN}初始化完成！${NC}"
echo "========================================"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，配置数据库和 API Key"
echo "2. 如果使用 Docker: docker-compose up -d"
echo "3. 如果本地运行：uvicorn app.main:app --reload"
echo "4. 访问 http://localhost:8000/docs 查看 API 文档"
echo ""
