#!/usr/bin/env python3
"""
Demo 数据初始化脚本。
用法: python scripts/seed_demo_data.py

创建:
  - 1 个 admin 用户 (admin@example.com / Admin@123)
  - 1 个普通用户 (user@example.com / User@123)
  - 5 个商品
  - 3 个兑换码
  - 可选: 若干 usage record（需要先有 api_key）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User
from app.models.product import Product
from app.models.redeem import RedeemCode
from app.models.api_key import APIKey
from app.models.usage import UsageRecord


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ---- Admin 用户 ----
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("Admin@123"),
                status="active",
                role="admin",
                balance=Decimal("100"),
                available_balance=Decimal("100"),
            )
            db.add(admin)
            db.flush()
            print("✅ Admin 用户: admin@example.com / Admin@123 (role=admin)")
        else:
            print("⏩ Admin 用户已存在 (role=%s)" % admin.role)

        # ---- 普通用户 ----
        user = db.query(User).filter(User.email == "user@example.com").first()
        if not user:
            # 确保 username 不冲突
            base_username = "demouser"
            username = base_username
            counter = 0
            while db.query(User).filter(User.username == username).first():
                counter += 1
                username = f"{base_username}{counter}"
            user = User(
                username=username,
                email="user@example.com",
                password_hash=hash_password("User@123"),
                status="active",
                role="user",
                balance=Decimal("50"),
                available_balance=Decimal("50"),
            )
            db.add(user)
            db.flush()
            print("✅ 普通用户: user@example.com / User@123 (balance=$50, username=%s)" % username)
        else:
            print("⏩ 普通用户已存在 (balance=$%.2f)" % float(user.balance))

        # ---- API Key (给普通用户) ----
        key = db.query(APIKey).filter(APIKey.user_id == user.id, APIKey.name == "Demo Key").first()
        if not key:
            key = APIKey(
                user_id=user.id,
                name="Demo Key",
                key_value="sk-demo-key-12345678",
                group_name="Anthropic",
                status="active",
            )
            db.add(key)
            db.flush()
            print(f"✅ API Key 已创建 (id={key.id})")
        else:
            print("⏩ API Key 已存在")

        # ---- 商品 ----
        products_data = [
            ("Claude Pro 月卡", "claude-pro-monthly", "会员服务", "热销", 299.0, 999, "auto"),
            ("GPT-4o 算力包 1000 Tokens", "gpt4o-tokens-1000", "算力充值", None, 9.9, 9999, "auto"),
            ("Claude Sonnet 算力包 5000 Tokens", "claude-sonnet-5000", "算力充值", "推荐", 39.0, 9999, "auto"),
            ("团队月卡（5人）", "team-monthly-5", "会员服务", None, 999.0, 100, "manual"),
            ("年度会员", "annual-vip", "会员服务", "限定", 1999.0, 50, "auto"),
        ]
        for name, slug, cat, tag, price, stock, delivery in products_data:
            existing = db.query(Product).filter(Product.slug == slug).first()
            if not existing:
                p = Product(
                    name=name, slug=slug, category=cat, tag=tag,
                    price_cny=price, stock=stock, delivery_type=delivery,
                    is_active=True, sort_order=0,
                )
                db.add(p)
                print(f"✅ 商品: {name}")
            else:
                print(f"⏩ 商品已存在: {name}")

        # ---- 兑换码 ----
        codes_data = [
            ("WELCOME10", Decimal("10"), "balance"),
            ("SUMMER50", Decimal("50"), "balance"),
            ("VIP100", Decimal("100"), "balance"),
        ]
        for code, amount, rtype in codes_data:
            existing = db.query(RedeemCode).filter(RedeemCode.code == code).first()
            if not existing:
                rc = RedeemCode(
                    code=code,
                    reward_type=rtype,
                    reward_amount=amount,
                    is_used=0,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                )
                db.add(rc)
                print(f"✅ 兑换码: {code} = ${amount}")
            else:
                print(f"⏩ 兑换码已存在: {code}")

        # ---- Usage Records (给普通用户) ----
        if key:
            now = datetime.now(timezone.utc)
            usage_data = [
                (key.id, "claude-sonnet-4-20250514", 1200, 800, 2000, 0.012, 450),
                (key.id, "claude-sonnet-4-20250514", 500, 300, 800, 0.005, 320),
                (key.id, "gpt-4o", 2000, 1500, 3500, 0.021, 680),
            ]
            for kid, model, inp, out, total, cost, lat in usage_data:
                rec = UsageRecord(
                    user_id=user.id, api_key_id=kid, model_name=model,
                    input_tokens=inp, output_tokens=out, total_tokens=total,
                    cost=Decimal(str(cost)), latency_ms=lat,
                    requested_at=now - timedelta(hours=2),
                )
                db.add(rec)
            print(f"✅ Usage Records: {len(usage_data)} 条已创建")

        db.commit()
        print("\n🎉 数据初始化完成！")
        print("\n测试账号:")
        print("  Admin:  admin@example.com  / Admin@123")
        print("  User:   user@example.com   / User@123")
        print("\n兑换码: WELCOME10 ($10) | SUMMER50 ($50) | VIP100 ($100)")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
