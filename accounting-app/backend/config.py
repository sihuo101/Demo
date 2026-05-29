"""应用配置"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用设置"""

    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/accounting_db"
    )

    # LLM 配置
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai_compatible")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    # 应用配置
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]


# 创建全局设置实例
settings = Settings()
