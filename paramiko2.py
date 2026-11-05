
# -*- coding: utf-8 -*-
import os
import time
import stat
import logging
import paramiko

# 로그 설정
logging.basicConfig(
    filename='sftp_error.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)

HOST = '192.168.0.100'
PORT = 22
USERNAME = 'user'
PASSWORD = 'password'

REMOTE_DIR = '/remote/data'
LOCAL_DIR = r'C:\download'
MAX_RETRIES = 3


def connect_sftp():
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()

    ssh.connect(
        hostname=HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
        timeout=15,
        allow_agent=False,
        look_for_keys=False
    )

    sftp = ssh.open_sftp()
    return ssh, sftp


def close_sftp(ssh, sftp):
    if sftp is not None:
        try:
            sftp.close()
        except Exception:
            logging.exception('SFTP close failed')

    if ssh is not None:
        try:
            ssh.close()
        except Exception:
            logging.exception('SSH close failed')


def download_file(ssh, sftp, filename, remote_size):
    remote_path = REMOTE_DIR.rstrip('/') + '/' + filename
    local_path = os.path.join(LOCAL_DIR, filename)
    temp_path = local_path + '.part'

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 임시 파일로 다운로드
            if os.path.exists(temp_path):
                os.remove(temp_path)

            sftp.get(remote_path, temp_path)

            # 파일 크기 검증
            actual_size = os.path.getsize(temp_path)

            if actual_size != remote_size:
                raise IOError(
                    'Size mismatch: expected=%d actual=%d'
                    % (remote_size, actual_size)
                )

            # 검증이 끝난 파일만 최종 경로로 이동
            if os.path.exists(local_path):
                os.remove(local_path)

            os.rename(temp_path, local_path)

            logging.info(
                'SUCCESS: %s (%d bytes)',
                filename, actual_size
            )
            print('완료:', filename)
            return True

        except Exception:
            logging.exception(
                'DOWNLOAD FAILED: %s attempt=%d/%d',
                filename, attempt, MAX_RETRIES
            )

            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    logging.exception('TEMP FILE REMOVE FAILED')

            if attempt < MAX_RETRIES:
                # 연결 오류일 수 있으므로 기존 연결을 교체
                close_sftp(ssh, sftp)
                time.sleep(attempt * 2)

                try:
                    new_ssh, new_sftp = connect_sftp()
                    ssh = new_ssh
                    sftp = new_sftp
                except Exception:
                    logging.exception('RECONNECT FAILED')
                    # 다음 시도에서도 재연결을 시도하도록 함
                    ssh = None
                    sftp = None

    logging.error('GIVE UP: %s', filename)
    print('실패:', filename)
    return False, ssh, sftp


def main():
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)

    ssh = None
    sftp = None
    failed = []

    try:
        ssh, sftp = connect_sftp()
        attrs = sftp.listdir_attr(REMOTE_DIR)

        # 일반 파일만 다운로드
        files = [
            item for item in attrs
            if stat.S_ISREG(item.st_mode)
        ]

        print('전체 파일 수:', len(files))

        for item in files:
            # 연결이 없으면 다시 생성
            if ssh is None or sftp is None:
                try:
                    ssh, sftp = connect_sftp()
                except Exception:
                    logging.exception('CONNECT FAILED')
                    failed.append(item.filename)
                    continue

            result = download_file(
                ssh, sftp, item.filename, item.st_size
            )

            # 다운로드 함수의 반환값 처리
            if isinstance(result, tuple):
                success, ssh, sftp = result
            else:
                success = result

            if not success:
                failed.append(item.filename)

    except Exception:
        logging.exception('MAIN PROCESS FAILED')
        raise

    finally:
        close_sftp(ssh, sftp)

    print('다운로드 완료')
    print('실패 파일 수:', len(failed))

    if failed:
        print('실패 목록:')
        for filename in failed:
            print(filename)

        logging.error('FAILED FILES: %r', failed)


if __name__ == '__main__':
    main()
