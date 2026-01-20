# -*- coding: utf-8 -*-
import codecs

file_path = '평가문제_1-18차시.csv'

# 파일을 바이너리 모드로 읽기
with open(file_path, 'rb') as f:
    content = f.read()

# BOM이 없으면 추가
if not content.startswith(codecs.BOM_UTF8):
    # UTF-8 BOM 추가
    with open(file_path, 'wb') as f:
        f.write(codecs.BOM_UTF8 + content)
    print("UTF-8 BOM이 추가되었습니다.")
else:
    print("이미 UTF-8 BOM이 포함되어 있습니다.")



