import logging

# 로거 생성
logger = logging.getLogger('sftp')
logger.setLevel(logging.DEBUG)

# 로그 형식
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)

# 성공 로그 파일
success_handler = logging.FileHandler('success.log')
success_handler.setLevel(logging.INFO)
success_handler.setFormatter(formatter)

# 오류 로그 파일
error_handler = logging.FileHandler('error.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# 로거에 핸들러 등록
logger.addHandler(success_handler)
logger.addHandler(error_handler)

# 로그 기록
logger.info('파일 다운로드 성공')
logger.warning('다운로드 재시도')
logger.error('파일 다운로드 실패')
