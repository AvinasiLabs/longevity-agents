import sys
from loguru import logger as loguru_logger
import os

# 假设项目根路径为当前工作目录
project_root = os.getcwd()


def relative_path_formatter(record):
    # 获取绝对路径
    abs_path = record["file"].path
    # 计算相对路径
    rel_path = os.path.relpath(abs_path, project_root)
    # 替换 record 中的 file 字段
    record["file"] = rel_path
    return record


loguru_logger.remove(0)
loguru_logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level><cyan>{file}</cyan>:<cyan>{line}</cyan></level> | <level>{message}</level>",
    filter=relative_path_formatter,
)
logger = loguru_logger
