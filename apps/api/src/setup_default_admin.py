"""aios_api.setup_default_admin —— 启动时创建默认 admin 用户。

逻辑：
  - 如 users 表为空 → 创建 admin 账号（密码随机生成）
  - 打印到 stderr（docker logs 可见）
  - 强烈建议客户首次登录后改密码
"""
from __future__ import annotations

import asyncio
import os
import secrets
import string
import sys
import uuid
from pathlib import Path

# 让 `import aios_api.xxx` 能找到（src/ 不是命名包根时）
src_path = Path(__file__).resolve().parent
sys.path.insert(0, str(src_path))

from sqlalchemy import select  # noqa: E402

from aios_api.auth import hash_password  # noqa: E402
from aios_api.db import get_session, init_engine  # noqa: E402
from aios_api.models import User, UserRole  # noqa: E402


def _gen_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def main() -> int:
    init_engine()
    async for session in get_session():
        result = await session.execute(select(User))
        if result.scalar_one_or_none() is not None:
            print("[setup_default_admin] users exist, skip", file=sys.stderr)
            return 0
        username = os.getenv("AIOS_DEFAULT_ADMIN_USER", "admin")
        password = os.getenv("AIOS_DEFAULT_ADMIN_PASSWORD") or _gen_password()
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.commit()
        print("\n" + "=" * 60, file=sys.stderr)
        print("[setup_default_admin] 默认管理员账号已创建：", file=sys.stderr)
        print(f"  username: {username}", file=sys.stderr)
        print(f"  password: {password}", file=sys.stderr)
        print("  请立刻登录并修改密码！", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
