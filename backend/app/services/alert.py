"""消息告警：钉钉 / 企业微信机器人 Webhook 推送"""
import json
from datetime import datetime

import requests

from app.models import SystemConfig


def _get_config(db, key: str) -> str:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return row.value if row else ""


def _post_webhook(url: str, payload: dict) -> bool:
    if not url:
        return False
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def notify_failure(db, task, error: str):
    """任务失败推送告警（未配置 Webhook 时静默跳过）"""
    ding = _get_config(db, "dingtalk_webhook")
    wechat = _get_config(db, "wechat_webhook")
    if not ding and not wechat:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"## ⚠️ ETL 同步任务执行失败\n"
        f"> **任务名称**: {task.name}\n"
        f"> **执行时间**: {now}\n"
        f"> **失败原因**: {error[:500]}\n"
    )
    if ding:
        _post_webhook(ding, {"msgtype": "markdown", "markdown": {"content": text}})
    if wechat:
        _post_webhook(wechat, {"msgtype": "markdown", "markdown": {"content": text}})
