"""
Slack/Discord 알림 발송 모듈

Webhook을 통해 Slack과 Discord로 알림을 발송합니다.
"""

import requests
import json
import time
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime


def send_with_retry(send_func: Callable, *args, max_retries: int = 3, **kwargs) -> bool:
    """
    지수 백오프로 Webhook 재시도

    Args:
        send_func: 실행할 함수
        max_retries: 최대 재시도 횟수 (기본 3회)
        *args, **kwargs: send_func에 전달할 인자

    Returns:
        bool: 성공 여부
    """
    for attempt in range(max_retries):
        try:
            result = send_func(*args, **kwargs)
            if result:
                if attempt > 0:
                    print(f"[Webhook Retry Success] {attempt + 1}번째 시도에서 성공")
                return True
        except Exception as e:
            print(f"[Webhook Retry] {attempt + 1}번째 시도 실패: {e}")

        # 마지막 시도가 아니면 대기
        if attempt < max_retries - 1:
            delay = 2 ** attempt  # 1초, 2초, 4초
            print(f"[Webhook Retry] {delay}초 후 재시도...")
            time.sleep(delay)

    print(f"[Webhook Retry Failed] {max_retries}번 시도 후 실패")
    return False


def send_slack_notification(message: str, webhook_url: str, timeout: int = 5) -> bool:
    """
    Slack Webhook으로 알림 발송

    Args:
        message: 발송할 메시지 (dict or str)
        webhook_url: Slack Webhook URL
        timeout: 요청 타임아웃 (초)

    Returns:
        bool: 성공 여부
    """
    try:
        if isinstance(message, str):
            payload = {"text": message}
        else:
            payload = message

        response = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout
        )

        if response.status_code == 200:
            return True
        else:
            print(f"[Slack Webhook Error] Status: {response.status_code}, Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"[Slack Webhook Timeout] URL: {webhook_url}")
        return False
    except Exception as e:
        print(f"[Slack Webhook Exception] {str(e)}")
        return False


def send_discord_notification(message: str, webhook_url: str, timeout: int = 5) -> bool:
    """
    Discord Webhook으로 알림 발송

    Args:
        message: 발송할 메시지 (dict or str)
        webhook_url: Discord Webhook URL
        timeout: 요청 타임아웃 (초)

    Returns:
        bool: 성공 여부
    """
    try:
        if isinstance(message, str):
            payload = {"content": message}
        else:
            payload = message

        response = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout
        )

        if response.status_code in [200, 204]:
            return True
        else:
            print(f"[Discord Webhook Error] Status: {response.status_code}, Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"[Discord Webhook Timeout] URL: {webhook_url}")
        return False
    except Exception as e:
        print(f"[Discord Webhook Exception] {str(e)}")
        return False


def format_margin_alert(
    product_name: str,
    sourcing_price: float,
    selling_price: float,
    loss: float
) -> Dict:
    """
    역마진 경고 메시지 포맷팅

    Returns:
        Slack용과 Discord용 메시지를 포함한 dict
    """
    # Slack Block Kit 형식
    slack_message = {
        "text": "⚠️ 역마진 발생!",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ 역마진 발생 경고"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*상품명:*\n{product_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*손실 금액:*\n{int(loss):,}원"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*소싱가:*\n{int(sourcing_price):,}원"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*판매가:*\n{int(selling_price):,}원"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"발생 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # Discord Embed 형식
    discord_message = {
        "embeds": [{
            "title": "⚠️ 역마진 발생 경고",
            "color": 16711680,  # Red
            "fields": [
                {"name": "상품명", "value": product_name, "inline": False},
                {"name": "소싱가", "value": f"{int(sourcing_price):,}원", "inline": True},
                {"name": "판매가", "value": f"{int(selling_price):,}원", "inline": True},
                {"name": "손실 금액", "value": f"-{int(loss):,}원", "inline": True}
            ],
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_rpa_alert(
    order_number: str,
    source: str,
    status: str,
    execution_time: float,
    product_name: Optional[str] = None,
    error: Optional[str] = None
) -> Dict:
    """
    RPA 실행 결과 알림 메시지 포맷팅

    Args:
        status: 'success' or 'failed'
    """
    is_success = status == 'success'
    emoji = "✅" if is_success else "❌"
    color = 3066993 if is_success else 15158332  # Green or Red

    # Slack Block Kit 형식
    slack_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} RPA 자동 발주 {'' if is_success else '실패'}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*주문번호:*\n{order_number}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*소싱처:*\n{source.upper()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*실행 시간:*\n{execution_time:.2f}초"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*상태:*\n{'성공' if is_success else '실패'}"
                }
            ]
        }
    ]

    if product_name:
        slack_blocks.insert(1, {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*상품:* {product_name}"
            }
        })

    if error and not is_success:
        slack_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*오류:*\n```{error[:500]}```"  # 최대 500자
            }
        })

    slack_blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"발생 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
    })

    slack_message = {
        "text": f"{emoji} RPA 자동 발주 {'성공' if is_success else '실패'}: {order_number}",
        "blocks": slack_blocks
    }

    # Discord Embed 형식
    discord_fields = [
        {"name": "주문번호", "value": order_number, "inline": True},
        {"name": "소싱처", "value": source.upper(), "inline": True},
        {"name": "실행 시간", "value": f"{execution_time:.2f}초", "inline": True}
    ]

    if product_name:
        discord_fields.insert(0, {"name": "상품", "value": product_name, "inline": False})

    if error and not is_success:
        discord_fields.append({"name": "오류", "value": error[:1000], "inline": False})  # 최대 1000자

    discord_message = {
        "embeds": [{
            "title": f"{emoji} RPA 자동 발주 {'성공' if is_success else '실패'}",
            "color": color,
            "fields": discord_fields,
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_order_sync_alert(
    market: str,
    collected_count: int,
    success_count: int,
    fail_count: int
) -> Dict:
    """
    주문 동기화 완료 알림 메시지 포맷팅
    """
    # Slack Block Kit 형식
    slack_message = {
        "text": f"📦 주문 수집 완료: {success_count}건",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📦 주문 수집 완료"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*마켓:*\n{market}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*수집 건수:*\n{collected_count}건"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*성공:*\n{success_count}건"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*실패:*\n{fail_count}건"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"동기화 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # Discord Embed 형식
    discord_message = {
        "embeds": [{
            "title": "📦 주문 수집 완료",
            "color": 3447003,  # Blue
            "fields": [
                {"name": "마켓", "value": market, "inline": True},
                {"name": "수집 건수", "value": f"{collected_count}건", "inline": True},
                {"name": "성공", "value": f"{success_count}건", "inline": True},
                {"name": "실패", "value": f"{fail_count}건", "inline": True}
            ],
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_price_change_alert(
    product_name: str,
    old_price: float,
    new_price: float,
    change_percent: float
) -> Dict:
    """
    가격 변동 알림 메시지 포맷팅
    """
    is_increase = new_price > old_price
    emoji = "📈" if is_increase else "📉"
    title = "가격 인상 감지" if is_increase else "가격 인하 감지"
    color = 15158332 if is_increase else 3066993  # Red if increase, Green if decrease

    # Slack Block Kit 형식
    slack_message = {
        "text": f"{emoji} {title}: {product_name}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*상품명:*\n{product_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*변동률:*\n{change_percent:+.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*이전 가격:*\n{int(old_price):,}원"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*현재 가격:*\n{int(new_price):,}원"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"감지 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # Discord Embed 형식
    discord_message = {
        "embeds": [{
            "title": f"{emoji} {title}",
            "color": color,
            "fields": [
                {"name": "상품명", "value": product_name, "inline": False},
                {"name": "이전 가격", "value": f"{int(old_price):,}원", "inline": True},
                {"name": "현재 가격", "value": f"{int(new_price):,}원", "inline": True},
                {"name": "변동률", "value": f"{change_percent:+.1f}%", "inline": True}
            ],
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_price_adjustment_alert(
    product_name: str,
    old_price: float,
    new_price: float,
    margin_rate: float,
    sourcing_price: float,
    playauto_updated: bool = False
) -> Dict:
    """
    자동 가격 조정 완료 알림 메시지 포맷팅
    """
    emoji = "💰"
    price_diff = new_price - old_price
    is_increase = price_diff > 0

    # Slack Block Kit 형식
    slack_message = {
        "text": f"{emoji} 자동 가격 조정: {product_name}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} 자동 가격 조정 완료"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*상품명:*\n{product_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*마진율:*\n{margin_rate:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*이전 판매가:*\n{int(old_price):,}원"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*새 판매가:*\n{int(new_price):,}원"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*소싱가:*\n{int(sourcing_price):,}원"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*PlayAuto:*\n{'✅ 동기화됨' if playauto_updated else '⏳ 로컬만'}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"조정 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # Discord Embed 형식
    color = 3066993 if playauto_updated else 15105570  # Green if synced, Orange if not

    discord_message = {
        "embeds": [{
            "title": f"{emoji} 자동 가격 조정 완료",
            "color": color,
            "fields": [
                {"name": "상품명", "value": product_name, "inline": False},
                {"name": "소싱가", "value": f"{int(sourcing_price):,}원", "inline": True},
                {"name": "이전 판매가", "value": f"{int(old_price):,}원", "inline": True},
                {"name": "새 판매가", "value": f"{int(new_price):,}원", "inline": True},
                {"name": "마진율", "value": f"{margin_rate:.1f}%", "inline": True},
                {"name": "가격 변동", "value": f"{'+' if is_increase else ''}{int(price_diff):,}원", "inline": True},
                {"name": "PlayAuto", "value": "✅ 동기화됨" if playauto_updated else "⏳ 로컬만", "inline": True}
            ],
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_bulk_price_adjustment_alert(
    adjusted_count: int,
    target_margin: float
) -> Dict:
    """
    일괄 가격 조정 완료 알림 메시지 포맷팅
    """
    emoji = "📊"

    # Slack Block Kit 형식
    slack_message = {
        "text": f"{emoji} 일괄 가격 조정 완료: {adjusted_count}개 상품",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} 일괄 가격 조정 완료"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*조정된 상품:*\n{adjusted_count}개"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*목표 마진율:*\n{target_margin}%"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"조정 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # Discord Embed 형식
    discord_message = {
        "embeds": [{
            "title": f"{emoji} 일괄 가격 조정 완료",
            "color": 5814783,  # Purple
            "fields": [
                {"name": "조정된 상품", "value": f"{adjusted_count}개", "inline": True},
                {"name": "목표 마진율", "value": f"{target_margin}%", "inline": True}
            ],
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_inventory_alert(
    product_name: str,
    alert_type: str,
    current_price: Optional[float] = None
) -> Dict:
    """
    재고 관리 알림 메시지 포맷팅

    Args:
        alert_type: 'out_of_stock' or 'restock'
    """
    is_restock = alert_type == 'restock'
    emoji = "✅" if is_restock else "🚫"
    title = "재입고 감지" if is_restock else "품절 감지"
    color = 3066993 if is_restock else 15844367  # Green or Orange

    # Slack Block Kit 형식
    slack_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {title}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*상품:* {product_name}"
            }
        }
    ]

    if is_restock and current_price:
        slack_blocks[1]["text"]["text"] += f"\n*현재 가격:* {int(current_price):,}원"
    elif not is_restock:
        slack_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚠️ 상품이 자동으로 비활성화되었습니다."
            }
        })

    slack_blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"감지 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
    })

    slack_message = {
        "text": f"{emoji} {title}: {product_name}",
        "blocks": slack_blocks
    }

    # Discord Embed 형식
    discord_fields = [
        {"name": "상품", "value": product_name, "inline": False}
    ]

    if is_restock and current_price:
        discord_fields.append({"name": "현재 가격", "value": f"{int(current_price):,}원", "inline": True})
    elif not is_restock:
        discord_fields.append({"name": "상태", "value": "자동 비활성화됨", "inline": False})

    discord_message = {
        "embeds": [{
            "title": f"{emoji} {title}",
            "color": color,
            "fields": discord_fields,
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_product_unavailable_alert(
    product_id: int,
    product_name: str,
    sourcing_url: str,
    status: str,
    details: str
) -> Dict:
    """
    소싱 상품 판매종료/삭제 알림 메시지 포맷팅
    """
    status_emoji = {
        'discontinued': '🚫',
        'out_of_stock': '📦',
        'error': '⚠️'
    }
    status_text = {
        'discontinued': '판매종료',
        'out_of_stock': '일시품절',
        'error': '오류'
    }

    emoji = status_emoji.get(status, '❓')
    status_label = status_text.get(status, status)

    # Slack Block Kit 형식
    slack_message = {
        "text": f"{emoji} 소싱 상품 {status_label}: {product_name}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} 소싱 상품 {status_label} 감지"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*상품 ID:*\n#{product_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*상태:*\n{status_label}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*상품명:*\n{product_name}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*소싱 URL:*\n{sourcing_url[:100]}..."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*상세:*\n{details}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"감지 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # 색상 설정
    color_map = {
        'discontinued': 15158332,  # Red
        'out_of_stock': 15844367,  # Orange
        'error': 16776960          # Yellow
    }
    color = color_map.get(status, 8421504)

    # Discord Embed 형식
    discord_message = {
        "embeds": [{
            "title": f"{emoji} 소싱 상품 {status_label} 감지",
            "color": color,
            "fields": [
                {"name": "상품 ID", "value": f"#{product_id}", "inline": True},
                {"name": "상태", "value": status_label, "inline": True},
                {"name": "상품명", "value": product_name, "inline": False},
                {"name": "소싱 URL", "value": sourcing_url[:200], "inline": False},
                {"name": "상세", "value": details, "inline": False}
            ],
            "footer": {
                "text": "소싱처에서 상품이 삭제되었거나 판매가 종료되었을 수 있습니다. 대체 소싱처를 확인하세요."
            },
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_price_fetch_fail_alert(
    product_id: int,
    product_name: str,
    sourcing_url: str,
    fail_count: int
) -> Dict:
    """
    가격 추출 연속 실패 알림 메시지 포맷팅
    """
    # Slack Block Kit 형식
    slack_message = {
        "text": f"⚠️ 가격 추출 {fail_count}회 연속 실패: {product_name}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️ 가격 추출 연속 실패 경고"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*상품 ID:*\n#{product_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*연속 실패:*\n{fail_count}회"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*상품명:*\n{product_name}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*소싱 URL:*\n{sourcing_url[:100]}..."
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"발생 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # Discord Embed 형식
    discord_message = {
        "embeds": [{
            "title": "⚠️ 가격 추출 연속 실패 경고",
            "color": 15105570,  # Orange
            "fields": [
                {"name": "상품 ID", "value": f"#{product_id}", "inline": True},
                {"name": "연속 실패", "value": f"{fail_count}회", "inline": True},
                {"name": "상품명", "value": product_name, "inline": False},
                {"name": "소싱 URL", "value": sourcing_url[:200], "inline": False}
            ],
            "footer": {
                "text": "소싱처 페이지 구조 변경 또는 접근 차단 가능성이 있습니다."
            },
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def format_new_order_alert(
    order_number: str,
    market: str,
    customer_name: str,
    total_amount: float,
    items: List[Dict]
) -> Dict:
    """
    새로운 주문 알림 메시지 포맷팅

    Args:
        order_number: 주문번호
        market: 마켓명 (coupang, naver, 11st 등)
        customer_name: 고객명
        total_amount: 총 주문금액
        items: 주문 상품 목록 [{"product_name": "...", "quantity": 1, "price": 10000}, ...]
    """
    market_emoji = {
        'coupang': '🛒',
        'naver': 'Ⓝ',
        '11st': '⑪',
        'gmarket': 'Ⓖ',
        'auction': 'Ⓐ',
        'homeplus': '🏪',
        'traders': '🏬',
        'otokimall': '🍜',
        'ssg': '🛍️',
        'cjthemarket': '🥘',
        'dongwonmall': '🐟'
    }
    emoji = market_emoji.get(market.lower(), '📦')

    # 상품 목록 텍스트 생성
    items_text = ""
    items_list = []
    for idx, item in enumerate(items, 1):
        product_name = item.get('product_name', '알 수 없음')
        quantity = item.get('quantity', 1)
        price = item.get('price', 0) or item.get('selling_price', 0)

        items_text += f"{idx}. {product_name} x {quantity}개 ({int(price):,}원)\n"
        items_list.append(f"• {product_name} x {quantity}개")

    # Slack Block Kit 형식
    slack_message = {
        "text": f"{emoji} 새로운 주문: {order_number}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} 새로운 주문 접수"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*주문번호:*\n{order_number}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*마켓:*\n{market.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*고객명:*\n{customer_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*총 금액:*\n{int(total_amount):,}원"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*주문 상품 ({len(items)}개):*\n{items_text.strip()}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"주문 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }

    # Discord Embed 형식
    discord_fields = [
        {"name": "주문번호", "value": order_number, "inline": True},
        {"name": "마켓", "value": market.upper(), "inline": True},
        {"name": "고객명", "value": customer_name, "inline": True},
        {"name": "총 금액", "value": f"{int(total_amount):,}원", "inline": True},
        {"name": f"주문 상품 ({len(items)}개)", "value": "\n".join(items_list[:10]), "inline": False}  # 최대 10개만 표시
    ]

    discord_message = {
        "embeds": [{
            "title": f"{emoji} 새로운 주문 접수",
            "color": 5814783,  # Purple
            "fields": discord_fields,
            "timestamp": datetime.now().isoformat()
        }]
    }

    return {"slack": slack_message, "discord": discord_message}


def send_notification(
    notification_type: str,
    message: str,
    **kwargs
) -> bool:
    """
    범용 알림 발송 함수

    Args:
        notification_type: 알림 유형 ('margin_alert', 'rpa_success', 'rpa_failure',
                          'order_sync', 'inventory_out_of_stock', 'inventory_restock')
        message: 기본 메시지 (포맷팅되지 않은 경우)
        **kwargs: 메시지 포맷팅에 필요한 추가 파라미터

    Returns:
        bool: 최소 하나의 Webhook 발송 성공 여부
    """
    try:
        # DB에서 활성화된 Webhook 설정 조회
        from database.db_wrapper import get_db
        db = get_db()
        webhooks = db.get_all_webhook_settings(enabled_only=True)

        if not webhooks:
            # Webhook 설정이 없으면 조용히 반환
            return False

        # 알림 유형별 메시지 포맷팅
        formatted_messages = None

        if notification_type == 'margin_alert':
            formatted_messages = format_margin_alert(
                product_name=kwargs.get('product_name', ''),
                sourcing_price=kwargs.get('sourcing_price', 0),
                selling_price=kwargs.get('selling_price', 0),
                loss=kwargs.get('loss', 0)
            )
        elif notification_type in ['rpa_success', 'rpa_failure']:
            status = 'success' if notification_type == 'rpa_success' else 'failed'
            formatted_messages = format_rpa_alert(
                order_number=kwargs.get('order_number', ''),
                source=kwargs.get('source', ''),
                status=status,
                execution_time=kwargs.get('execution_time', 0),
                product_name=kwargs.get('product_name'),
                error=kwargs.get('error')
            )
        elif notification_type == 'order_sync':
            formatted_messages = format_order_sync_alert(
                market=kwargs.get('market', '전체'),
                collected_count=kwargs.get('collected_count', 0),
                success_count=kwargs.get('success_count', 0),
                fail_count=kwargs.get('fail_count', 0)
            )
        elif notification_type in ['inventory_out_of_stock', 'inventory_restock']:
            alert_type = 'restock' if notification_type == 'inventory_restock' else 'out_of_stock'
            formatted_messages = format_inventory_alert(
                product_name=kwargs.get('product_name', ''),
                alert_type=alert_type,
                current_price=kwargs.get('current_price')
            )
        elif notification_type == 'price_change':
            formatted_messages = format_price_change_alert(
                product_name=kwargs.get('product_name', ''),
                old_price=kwargs.get('old_price', 0),
                new_price=kwargs.get('new_price', 0),
                change_percent=kwargs.get('change_percent', 0)
            )
        elif notification_type == 'price_adjustment':
            formatted_messages = format_price_adjustment_alert(
                product_name=kwargs.get('product_name', ''),
                old_price=kwargs.get('old_price', 0),
                new_price=kwargs.get('new_price', 0),
                margin_rate=kwargs.get('margin_rate', 0),
                sourcing_price=kwargs.get('sourcing_price', 0),
                playauto_updated=kwargs.get('playauto_updated', False)
            )
        elif notification_type == 'bulk_price_adjustment':
            formatted_messages = format_bulk_price_adjustment_alert(
                adjusted_count=kwargs.get('adjusted_count', 0),
                target_margin=kwargs.get('target_margin', 30.0)
            )
        elif notification_type == 'new_order':
            formatted_messages = format_new_order_alert(
                order_number=kwargs.get('order_number', ''),
                market=kwargs.get('market', ''),
                customer_name=kwargs.get('customer_name', ''),
                total_amount=kwargs.get('total_amount', 0),
                items=kwargs.get('items', [])
            )
        elif notification_type == 'price_fetch_fail':
            formatted_messages = format_price_fetch_fail_alert(
                product_id=kwargs.get('product_id', 0),
                product_name=kwargs.get('product_name', ''),
                sourcing_url=kwargs.get('sourcing_url', ''),
                fail_count=kwargs.get('fail_count', 0)
            )
        elif notification_type == 'product_unavailable':
            formatted_messages = format_product_unavailable_alert(
                product_id=kwargs.get('product_id', 0),
                product_name=kwargs.get('product_name', ''),
                sourcing_url=kwargs.get('sourcing_url', ''),
                status=kwargs.get('status', 'discontinued'),
                details=kwargs.get('details', '')
            )

        # Webhook 발송
        success_count = 0

        for webhook in webhooks:
            webhook_type = webhook['webhook_type']
            webhook_url = webhook['webhook_url']
            notification_types = webhook.get('notification_types', 'all')

            # 알림 타입 필터링
            if notification_types != 'all':
                try:
                    types_list = json.loads(notification_types) if isinstance(notification_types, str) else notification_types
                    if notification_type not in types_list and 'all' not in types_list:
                        continue
                except:
                    pass

            # 메시지 발송 (지수 백오프 재시도 포함)
            try:
                if formatted_messages:
                    msg = formatted_messages.get(webhook_type, message)
                else:
                    msg = message

                if webhook_type == 'slack':
                    result = send_with_retry(send_slack_notification, msg, webhook_url)
                elif webhook_type == 'discord':
                    result = send_with_retry(send_discord_notification, msg, webhook_url)
                else:
                    result = False

                # 로그 기록
                db.add_webhook_log(
                    webhook_id=webhook['id'],
                    notification_type=notification_type,
                    status='success' if result else 'failed',
                    message=message if not formatted_messages else json.dumps(formatted_messages),
                    error_details=None if result else "Webhook 발송 실패"
                )

                if result:
                    success_count += 1

            except Exception as e:
                # 개별 Webhook 실패는 로그만 남기고 계속 진행
                db.add_webhook_log(
                    webhook_id=webhook['id'],
                    notification_type=notification_type,
                    status='failed',
                    message=message,
                    error_details=str(e)
                )
                print(f"[Webhook Error] {webhook_type}: {str(e)}")

        return success_count > 0

    except Exception as e:
        # 전체 실패 시에도 메인 동작 차단하지 않음
        print(f"[Notification Error] {str(e)}")
        return False
