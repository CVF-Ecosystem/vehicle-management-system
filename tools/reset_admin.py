#!/usr/bin/env python3
"""
tools/reset_admin.py
====================
CLI tool để reset mật khẩu admin một cách an toàn.

Thay thế cơ chế unlock.txt không an toàn (đã bị xóa vì lý do bảo mật).

Yêu cầu: Chạy trực tiếp trên máy chủ với quyền truy cập file system.

Usage:
    python tools/reset_admin.py
    python tools/reset_admin.py --password <new_password>
    python tools/reset_admin.py --unlock-only  # Chỉ mở khóa, không đổi mật khẩu
"""

import sys
import os
import argparse
import getpass

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="Reset mật khẩu admin cho Vehicle Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python tools/reset_admin.py                    # Interactive mode
  python tools/reset_admin.py --unlock-only      # Chỉ mở khóa tài khoản
  python tools/reset_admin.py --password abc123  # Đặt mật khẩu cụ thể
        """
    )
    parser.add_argument(
        "--password", "-p",
        help="Mật khẩu mới (nếu không cung cấp, sẽ hỏi interactively)",
        default=None
    )
    parser.add_argument(
        "--unlock-only",
        action="store_true",
        help="Chỉ mở khóa tài khoản admin, không đổi mật khẩu"
    )
    parser.add_argument(
        "--username", "-u",
        help="Tên tài khoản cần reset (mặc định: admin)",
        default="admin"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Vehicle Management System — Admin Reset Tool")
    print("=" * 60)
    print()

    # Import after path setup
    try:
        from database.user_repository import UserRepository
        import config
    except ImportError as e:
        print(f"[ERROR] Không thể import module: {e}")
        print("Hãy chạy script từ thư mục gốc của dự án.")
        sys.exit(1)

    # Connect to security DB
    try:
        user_repo = UserRepository()
    except Exception as e:
        print(f"[ERROR] Không thể kết nối database: {e}")
        sys.exit(1)

    # Find admin user
    admin = user_repo.get_user_by_username(args.username)
    if not admin:
        print(f"[ERROR] Không tìm thấy tài khoản '{args.username}'")
        sys.exit(1)

    print(f"Tài khoản: {admin['username']}")
    print(f"Trạng thái: {'Hoạt động' if admin['is_active'] else 'Bị khóa'}")
    print(f"Số lần đăng nhập sai: {admin.get('failed_login_attempts', 0)}")
    print()

    # Unlock account
    if not admin['is_active'] or admin.get('failed_login_attempts', 0) > 0:
        print("[INFO] Đang mở khóa tài khoản...")
        user_repo._reset_failed_attempts(admin['id'])
        user_repo.update_user(admin['id'], is_active=True)
        print("[OK] Tài khoản đã được mở khóa.")

    if args.unlock_only:
        print("\n[DONE] Chỉ mở khóa tài khoản (không đổi mật khẩu).")
        return

    # Get new password
    if args.password:
        new_password = args.password
    else:
        print("Nhập mật khẩu mới (tối thiểu 6 ký tự):")
        new_password = getpass.getpass("  Mật khẩu mới: ")
        confirm = getpass.getpass("  Xác nhận mật khẩu: ")
        if new_password != confirm:
            print("[ERROR] Mật khẩu không khớp!")
            sys.exit(1)

    if len(new_password) < 6:
        print("[ERROR] Mật khẩu phải có ít nhất 6 ký tự!")
        sys.exit(1)

    # Change password
    result = user_repo.change_password(admin['id'], new_password)
    if result.get("success"):
        print(f"\n[OK] Đã đổi mật khẩu cho tài khoản '{args.username}' thành công.")
        print("[WARN] Hãy đổi mật khẩu ngay sau khi đăng nhập lần đầu!")
    else:
        print(f"[ERROR] Đổi mật khẩu thất bại: {result.get('message')}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Hoàn tất. Bạn có thể đăng nhập vào ứng dụng.")
    print("=" * 60)


if __name__ == "__main__":
    main()
