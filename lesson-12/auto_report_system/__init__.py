#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동매매 자동 리포트 생성 시스템
정기적으로 거래 데이터를 분석하고 리포트를 생성/발송하는 시스템
"""

__version__ = "1.0.0"
__author__ = "Auto Trading Team"

from .core.report_manager import ReportManager
from .core.scheduler import ReportScheduler

__all__ = ['ReportManager', 'ReportScheduler']

