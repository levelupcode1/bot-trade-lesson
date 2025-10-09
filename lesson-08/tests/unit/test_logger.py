"""
Logger 유틸리티 테스트
"""

import pytest
import tempfile
import logging
from pathlib import Path
from src.utils.logger import setup_logger


def test_logger_creation():
    """로거 생성 테스트"""
    logger = setup_logger("test_logger")
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO


def test_logger_with_file():
    """파일 로거 테스트"""
    # 임시 로그 파일
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        temp_log_path = f.name
    
    try:
        logger = setup_logger("file_logger", temp_log_path)
        logger.info("Test message")
        
        # 로그 파일 확인
        assert Path(temp_log_path).exists()
        
        with open(temp_log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
            assert "Test message" in log_content
            
    finally:
        # 임시 파일 삭제
        Path(temp_log_path).unlink()


def test_logger_levels():
    """로그 레벨 테스트"""
    logger = setup_logger("level_logger", level=logging.DEBUG)
    
    assert logger.level == logging.DEBUG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

