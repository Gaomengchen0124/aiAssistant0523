#!/bin/bash
echo "=== AI KOL Matcher 环境初始化 ==="
echo "检查 Python 版本..."
python --version || python3 --version

echo "安装依赖..."
pip install -r requirements.txt

echo "检查数据文件..."
if [ ! -f "data/influencers.csv" ]; then
    echo "警告：data/influencers.csv 不存在，请先准备达人数据"
else
    echo "数据文件已就绪"
fi

echo "初始化完成"
