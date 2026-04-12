#!/usr/bin/env python3
"""
Provider 健康检查脚本。
可手动运行或挂 cron：0 * * * * /path/to/run_health_checks.py

用法：
  python run_health_checks.py
  python run_health_checks.py --provider-id 1
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.provider import Provider
from app.core.healthcheck import sync_check_provider_health
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def run_all():
    db = SessionLocal()
    try:
        providers = db.query(Provider).filter(Provider.is_active == True).all()
        logger.info(f"Found {len(providers)} active providers")
        for p in providers:
            old = p.health_status
            new = sync_check_provider_health(p)
            p.health_status = new
            logger.info(f"Provider {p.id} ({p.name}): {old} -> {new}")
        db.commit()
        logger.info("Health check complete")
    finally:
        db.close()

def run_single(provider_id: int):
    db = SessionLocal()
    try:
        p = db.query(Provider).filter(Provider.id == provider_id).first()
        if not p:
            logger.error(f"Provider {provider_id} not found")
            return
        old = p.health_status
        new = sync_check_provider_health(p)
        p.health_status = new
        db.commit()
        logger.info(f"Provider {p.id} ({p.name}): {old} -> {new}")
    finally:
        db.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider-id', type=int, default=None)
    args = parser.parse_args()
    if args.provider_id:
        run_single(args.provider_id)
    else:
        run_all()
