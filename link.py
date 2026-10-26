## add main gui code

import ctypes


ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
app = QApplication(sys.argv)
app.setApplicationName(APP_NAME)
app.setWindowIcon(app_icon())

# ======================================================================================================
## make_link.py
import os
import pythoncom
from win32com.propsys import propsys, pscon
from win32com.shell import shell

app_id = "jaegwannoh.HabitCalendar"
app_name = "나의 습관 달력"
python_path = r"C:\anaconda3\pythonw.exe"
program_path = r"C:\Calendar_Planner\main.py"
icon_path = r"C:\Calendar_Planner\assets\app.ico"

# 바로가기 만들기: pythonw.exe 가 main.py 를 실행
link = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None,
                                  pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
link.SetPath(python_path)
link.SetArguments(f'"{program_path}"')
link.SetWorkingDirectory(os.path.dirname(program_path))
link.SetIconLocation(icon_path, 0)  # 앱 아이콘 (0 = 파일 안의 첫 번째 아이콘)

# 앱 이름표(app_id) 붙이기
store = link.QueryInterface(propsys.IID_IPropertyStore)
store.SetValue(pscon.PKEY_AppUserModel_ID, propsys.PROPVARIANTType(app_id))
store.Commit()

# 바탕화면에 저장
lnk_path = os.path.join(os.path.expanduser("~"), "Desktop", f"{app_name}.lnk")
link.QueryInterface(pythoncom.IID_IPersistFile).Save(lnk_path, 0)
print("바로가기 만듦:", lnk_path)

아이콘 파일을 프로그램 옆 assets 폴더에 둔다면 경로를 직접 적지 않아도 돼요. 
icon_path = os.path.join(os.path.dirname(program_path), "assets", "app.ico")로 쓰면
 program_path 기준으로 알아서 찾아요.
 
 # ======================================================================================================
 ## make_link_py27.py
 
 # -*- coding: utf-8 -*-
from __future__ import print_function
import os
import pythoncom
from win32com.propsys import propsys, pscon
from win32com.shell import shell

app_id = u"jaegwannoh.HabitCalendar"
app_name = u"나의 습관 달력"
python_path = u"C:\\anaconda2\\pythonw.exe"
program_path = u"C:\\Calendar_Planner\\main.py"
icon_path = u"C:\\Calendar_Planner\\assets\\app.ico"

# 바로가기 만들기: pythonw.exe 가 main.py 를 실행
link = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None,
                                  pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
link.SetPath(python_path)
link.SetArguments(u'"%s"' % program_path)
link.SetWorkingDirectory(os.path.dirname(program_path))
link.SetIconLocation(icon_path, 0)  # 앱 아이콘 (0 = 파일 안의 첫 번째 아이콘)

# 앱 이름표(app_id) 붙이기 (유니코드 문자열 형식으로)
store = link.QueryInterface(propsys.IID_IPropertyStore)
store.SetValue(pscon.PKEY_AppUserModel_ID,
               propsys.PROPVARIANTType(app_id, pythoncom.VT_LPWSTR))
store.Commit()

# 바탕화면에 저장
lnk_path = os.path.join(os.path.expanduser(u"~"), u"Desktop", app_name + u".lnk")
link.QueryInterface(pythoncom.IID_IPersistFile).Save(lnk_path, 0)
print(u"바로가기 만듦:", lnk_path)

- 파이썬 경로: python_path는 실제 2.7 Anaconda가 깔:\anaconda2 또는 C:\Users\<이름>\Anaconda2예요.
- 앱 쪽 코드도 2.7이면: main.py의 SetCurrentProcessExplicitAppUserModelID(...)에도 u"jaegwannoh.HabitCalendar"처럼 
유니코드로 넘겨야 해요. 그냥 문자열을 넘기면 이름표가 깨져서 바로가기와 짝이 맞지 않아요.
