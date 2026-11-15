"""Interactive one-time admin bootstrap. Secrets are not printed or committed."""
import getpass, os
from sqlalchemy import select
from .main import app
from .models import User
from .security import password_hash

def main():
    dbmaker=app.state.dbmaker
    username=input('Tên quản trị (mặc định admin): ').strip() or 'admin'
    fullname=input('Họ tên: ').strip() or 'Quản trị hệ thống'
    secret=getpass.getpass('Mật khẩu (>=12 ký tự): ')
    with dbmaker() as s:
        if s.scalar(select(User).where(User.username==username)):
            print('Tài khoản đã tồn tại. Không thay đổi mật khẩu.');return
        s.add(User(username=username,full_name=fullname,password_hash=password_hash(secret),global_role='admin'))
        s.commit()
    print('Đã tạo tài khoản quản trị. Không lưu mật khẩu trong mã nguồn.')

if __name__=='__main__': main()
