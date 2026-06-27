from __future__ import annotations

from oncall_rag.config import Config, load_config


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.llm_provider == "omlx"
        assert config.omlx_endpoint == "http://localhost:11434"
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50
        assert config.top_k == 5
        assert config.embedding_model == "all-MiniLM-L6-v2"

    def test_invalid_provider_raises(self):
        try:
            Config(llm_provider="invalid")
            assert False, "Should have raised"
        except ValueError as e:
            assert "Invalid LLM provider" in str(e)

    def test_openai_key_not_required_by_default(self):
        config = Config(llm_provider="openai")
        assert config.openai_api_key is None

    def test_overrides(self):
        config = Config(llm_provider="openai", top_k=10, chunk_size=1000)
        assert config.llm_provider == "openai"
        assert config.top_k == 10
        assert config.chunk_size == 1000


class TestLoadConfig:
    def test_returns_defaults_when_no_env_file(self, tmp_path):
        config = load_config(env_file=str(tmp_path / ".env"))
        assert config.llm_provider == "omlx"

    def test_loads_from_env_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("LLM_PROVIDER=openai\nTOP_K=3\n")
        config = load_config(env_file=str(env_file))
        assert config.llm_provider == "openai"
        assert config.top_k == 3
        assert config.chunk_size == 500  # default

    def test_ignores_unknown_env_vars(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("UNKNOWN_VAR=foo\nTOP_K=7\n")
        config = load_config(env_file=str(env_file))
        assert config.top_k == 7
