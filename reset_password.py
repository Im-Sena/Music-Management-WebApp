#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
パスワード変更スクリプト

使用方法:
    python reset_password.py <ユーザー名>
    例: python reset_password.py john

ユーザーが忘れたパスワードをリセット（変更）します。
新しいパスワードはプロンプトで入力します。
"""

import sqlite3
import hashlib
import sys
import getpass

def hash_password(password):
    """パスワードをSHA256でハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def reset_password(username):
    """
    ユーザーのパスワードをリセット
    
    Args:
        username: ユーザー名
    """
    
    # ============================================================
    # ユーザーの存在確認
    # ============================================================
    conn = sqlite3.connect("music.db")
    c = conn.cursor()
    
    # ユーザーが存在するか確認
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user:
        print(f"エラー: ユーザー '{username}' が見つかりません")
        conn.close()
        sys.exit(1)
    
    # ============================================================
    # 新しいパスワード入力
    # ============================================================
    print(f"\nユーザー '{username}' のパスワードをリセットします")
    
    while True:
        new_password = getpass.getpass("新しいパスワードを入力: ")
        
        if not new_password:
            print("エラー: パスワードは空にできません")
            continue
        
        confirm_password = getpass.getpass("パスワードを再入力: ")
        
        if new_password != confirm_password:
            print("エラー: パスワードが一致しません\n")
            continue
        
        break
    
    # ============================================================
    # パスワード更新
    # ============================================================
    hashed_password = hash_password(new_password)
    
    try:
        c.execute("""
            UPDATE users SET password = ? WHERE username = ?
        """, (hashed_password, username))
        conn.commit()
        
        print(f"\n✓ パスワードが正常に変更されました")
        print(f"  ユーザー: {username}")
        print(f"  新しいパスワードでログインできるようになりました\n")
        
    except sqlite3.Error as e:
        print(f"エラー: {str(e)}")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    # コマンドライン引数を確認
    if len(sys.argv) < 2:
        print("使用方法: python reset_password.py <ユーザー名>")
        print("例: python reset_password.py john")
        sys.exit(1)
    
    username = sys.argv[1]
    reset_password(username)
