"""
ConfigManager 클래스 테스트
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from src.core.config_manager import ConfigManager


def test_config_manager_initialization():
    """설정 관리자 초기화 테스트"""
    config_manager = ConfigManager("config/config.yaml")
    
    assert config_manager.config_path == Path("config/config.yaml")
    assert config_manager.config == {}


def test_config_validation():
    """설정 검증 테스트"""
    config_manager = ConfigManager()
    
    # 유효한 설정
    valid_config = {
        "api": {
            "upbit": {
                "access_key": "test_key",
                "secret_key": "test_secret"
            }
        }
    }
    
    # TODO: 구현 완료 후 주석 해제
    # assert config_manager.validate_config(valid_config) == True


def test_config_load_save():
    """설정 로드/저장 테스트"""
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        test_config = {
            "test_key": "test_value",
            "nested": {
                "key": "value"
            }
        }
        yaml.dump(test_config, f)
        temp_path = f.name
    
    try:
        config_manager = ConfigManager(temp_path)
        
        # TODO: 구현 완료 후 주석 해제
        # loaded_config = config_manager.load_config()
        # assert loaded_config["test_key"] == "test_value"
        
    finally:
        # 임시 파일 삭제
        Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

