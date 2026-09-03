"""Application configuration using Pydantic Settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """NexusPulse System Settings."""

    # Project metadata
    app_name: str = "NexusPulse"
    debug: bool = False

    # LLM Configuration (DeepSeek / OpenAI compatible)
    llm_provider: str = Field(default="deepseek", description="LLM provider type")
    openai_api_key: str = Field(default="", description="API key for OpenAI/DeepSeek")
    openai_base_url: str = Field(
        default="https://api.deepseek.com/v1", description="API base URL"
    )
    llm_model: str = Field(default="deepseek-chat", description="LLM model name")
    temperature: float = Field(default=0.2, description="Sampling temperature")

    # Knowledge Base & Obsidian Output
    obsidian_vault_path: Path = Field(
        default=Path("/Users/pluto/MyNotes/Projects/NexusPulse"),
        description="Path to output Obsidian notes",
    )

    # Database & Storage
    database_url: str = Field(
        default="postgresql+asyncpg://pluto:plutolab_secret@localhost:5432/nexuspulse",
        description="Database connection URL",
    )
    use_mock_db: bool = Field(
        default=True,
        description="Fallback to in-memory/SQLite store if Postgres is unavailable",
    )

    # Agent Pipeline Parameters
    triage_threshold: float = Field(
        default=7.0, description="Minimum score (out of 10) to trigger deep investigation"
    )
    max_critic_attempts: int = Field(
        default=3, description="Maximum review and refinement attempts in Critic loop"
    )

    # Hybrid Search & Time-Decay Parameters
    dense_weight: float = Field(default=0.7, description="Weight alpha for dense vector similarity")
    sparse_weight: float = Field(default=0.3, description="Weight (1-alpha) for sparse text similarity")
    time_decay_lambda: float = Field(
        default=0.005, description="Exponential decay factor per hour (Newton cooling decay)"
    )

    # Podcast Generation
    podcast_voice_host_a: str = Field(
        default="zh-CN-YunxiNeural", description="Edge-TTS voice for Host A (Inquisitive Lead)"
    )
    podcast_voice_host_b: str = Field(
        default="zh-CN-YunjianNeural", description="Edge-TTS voice for Host B (Critical Tech Veteran)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
