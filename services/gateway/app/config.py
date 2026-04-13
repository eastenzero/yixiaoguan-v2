from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """v2 Gateway 配置"""

    # -- 数据库 --
    database_url: str = "postgresql+asyncpg://yxg:yxg_v2_pass@localhost:5432/yixiaoguan_v2"
    redis_url: str = "redis://localhost:6379/1"

    # -- JWT --
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72

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

settings = Settings()
