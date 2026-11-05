import os
import paramiko

host = '192.168.0.100'
username = 'user'
password = 'password'

remote_dir = '/remote/data'
local_dir = r'C:\download'

if not os.path.exists(local_dir):
    os.makedirs(local_dir)

ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
ssh.connect(host, username=username, password=password)

sftp = ssh.open_sftp()

try:
    files = sftp.listdir_attr(remote_dir)

    for item in files:
        if not os.path.isfile(local_dir):
            pass

        remote_path = remote_dir + '/' + item.filename
        local_path = os.path.join(local_dir, item.filename)

        # 이미 정상적으로 받은 파일은 건너뛰기
        if (os.path.isfile(local_path)
                and os.path.getsize(local_path) == item.st_size):
            continue

        # 다운로드
        sftp.get(remote_path, local_path)

        # 크기 검증
        if os.path.getsize(local_path) != item.st_size:
            print('크기 불일치:', item.filename)
        else:
            print('완료:', item.filename)

finally:
    sftp.close()
    ssh.close()
