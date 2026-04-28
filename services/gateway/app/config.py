from pydantic_settings import BaseSettings

# 已知弱密钥黑名单 — 启动时若 jwt_secret 落在此集合或长度过短，直接抛错。
# 防止部署遗忘留下硬编码占位符（参见 2026-04-28 审计 .tasks/kimi-pilot-audit-report.md §3.1）。
_WEAK_JWT_SECRETS = {
    "change-me-in-production",
    "change-me",
    "secret",
    "your-secret-key",
}
_MIN_JWT_SECRET_LEN = 32


class Settings(BaseSettings):
    """v2 Gateway 配置"""

    # -- 数据库 --
    database_url: str = "postgresql+asyncpg://yxg:yxg_v2_pass@localhost:5432/yixiaoguan_v2"
    redis_url: str = "redis://localhost:6379/1"

    # -- JWT --
    # 必填，无默认值；启动时通过 _validate_jwt_secret 拒绝弱密钥。
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # -- Dify --
    dify_api_url: str = "http://localhost:5001/v1"
    dify_api_key: str = ""
    dify_global_dataset_id: str = ""
    dify_dataset_api_key: str = ""

    # -- 微信（P1 阶段） --
    wechat_mp_appid: str = ""
    wechat_mp_secret: str = ""
    wechat_work_corpid: str = ""
    wechat_work_agent_id: str = ""
    wechat_work_secret: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def _validate_jwt_secret(secret: str) -> None:
    if not secret or secret in _WEAK_JWT_SECRETS or len(secret) < _MIN_JWT_SECRET_LEN:
        raise RuntimeError(
            "JWT_SECRET 必须在 .env 中设置为强随机值 (长度 >= 32 字符，且非默认占位符)。\n"
            "生成方法：python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )


settings = Settings()
_validate_jwt_secret(settings.jwt_secret)
