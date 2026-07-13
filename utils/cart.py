"""
공통 장바구니 유틸리티 모듈
모든 페이지에서 import하여 사용합니다.
"""
import streamlit as st

from utils.html_safe import esc

EVENT_UNITS = {
    "1+1": 2,
    "2+1": 3,
    "3+1": 4,
}


def init_cart():
    if "cart" not in st.session_state:
        st.session_state.cart = {}


def add_to_cart(name: str, brand: str, event: str, price: int, unit_price: int):
    init_cart()
    key = (name, brand, event)
    if key in st.session_state.cart:
        st.session_state.cart[key]["qty"] += 1
    else:
        st.session_state.cart[key] = {
            "name": name,
            "brand": brand,
            "event": event,
            "unit_price": unit_price,
            "price": price,
            "qty": 1,
        }


def remove_from_cart(key):
    init_cart()
    if key in st.session_state.cart:
        del st.session_state.cart[key]


def is_in_cart(name: str, brand: str, event: str) -> bool:
    init_cart()
    return (name, brand, event) in st.session_state.cart


def get_cart_count() -> int:
    init_cart()
    return sum(v["qty"] for v in st.session_state.cart.values())


def calc_actual_total(price: int, event: str, qty: int) -> int:
    unit = EVENT_UNITS.get(event, 1)
    if unit == 1:
        return price * qty
    pay_needed = unit - 1
    sets = qty // pay_needed
    remainder = qty % pay_needed
    return price * (sets * pay_needed + remainder)


def calc_total_received(event: str, qty: int) -> int:
    if event == "1+1":
        return qty * 2
    if event == "2+1":
        return qty + qty // 2
    if event == "3+1":
        return qty + qty // 3
    return qty


def render_cart_warning(item: dict):
    event = item["event"]
    unit = EVENT_UNITS.get(event, 1)
    if unit == 1:
        return

    qty = item["qty"]
    pay_needed = unit - 1
    if qty % pay_needed == 0:
        return

    need = pay_needed - (qty % pay_needed)
    optimal_qty = qty + need
    optimal_total = item["price"] * pay_needed
    optimal_unit = optimal_total // unit
    current_unit = item["price"]
    event_esc = esc(event)

    st.markdown(
        f"""
        <div style="
            background: #2d1f00;
            border-left: 3px solid #ffaa00;
            border-radius: 6px;
            padding: 8px 10px;
            margin: 4px 0 8px 0;
            font-size: 0.8rem;
            color: #ffd280;
            line-height: 1.5;
        ">
            ⚠️ <b>{event_esc} 상품</b>이에요!<br>
            지금 {qty}개 → 개당 <b>{current_unit:,}원</b><br>
            {need}개 더 추가하면 ({optimal_qty}개) → 개당 <b>{optimal_unit:,}원</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_cart_button(row, button_key: str):
    init_cart()
    cart_key = (row["name"], row["brand"], row["event"])
    in_cart = cart_key in st.session_state.cart

    if in_cart:
        if st.button("✅ 담김", key=button_key, use_container_width=True):
            remove_from_cart(cart_key)
            st.rerun()
    else:
        if st.button("🛒 담기", key=button_key, use_container_width=True):
            add_to_cart(
                name=row["name"],
                brand=row["brand"],
                event=row["event"],
                price=int(row["price"]),
                unit_price=int(row["unit_price"]),
            )
            st.rerun()


def render_floating_cart():
    """우상단 🛒 — keyed container로 챗봇 FAB와 CSS 분리 (Streamlit 1.54 호환)."""
    init_cart()
    total_items = get_cart_count()

    st.markdown(
        """
        <style>
        div[class*="st-key-cvs_floating_cart"] div[data-testid="stPopover"] {
            position: fixed !important;
            top: 60px !important;
            right: 80px !important;
            bottom: auto !important;
            left: auto !important;
            width: auto !important;
            height: auto !important;
            z-index: 99999 !important;
        }
        div[class*="st-key-cvs_floating_cart"] div[data-testid="stPopover"] > div:first-child {
            width: auto !important;
            height: auto !important;
        }
        div[class*="st-key-cvs_floating_cart"] div[data-testid="stPopover"] button,
        div[class*="st-key-cvs_floating_cart"] [data-testid="stPopoverButton"] {
            background: linear-gradient(135deg, #ff6b6b, #ee5253) !important;
            color: white !important;
            border: none !important;
            border-radius: 24px !important;
            padding: 8px 20px !important;
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.45) !important;
            cursor: pointer !important;
            white-space: nowrap !important;
            width: auto !important;
            height: auto !important;
            min-width: auto !important;
        }
        div[class*="st-key-cvs_floating_cart"] div[data-testid="stPopover"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6) !important;
        }
        div[data-testid="stPopoverBody"]:not(:has([data-testid="stChatInput"])) {
            width: 380px !important;
            max-width: 90vw !important;
        }
        div[data-testid="stPopoverBody"]:not(:has([data-testid="stChatInput"]))
        [data-testid="stHorizontalBlock"] {
            gap: 0.4rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cart = st.session_state.cart
    badge = f"🛒 {total_items}개" if total_items > 0 else "🛒 0개"

    # popover() has no key on Streamlit 1.54 — scope CSS via keyed container
    with st.container(key="cvs_floating_cart"):
        with st.popover(badge):
            st.markdown("### 🛒 장바구니")

            if not cart:
                st.info("담긴 상품이 없습니다.")
                return

            total_price = 0
            total_saved = 0

            for key, item in list(cart.items()):
                item_total = calc_actual_total(item["price"], item["event"], item["qty"])
                total_received = calc_total_received(item["event"], item["qty"])
                unit_price_actual = (
                    item_total // total_received if total_received > 0 else item_total
                )
                total_price += item_total
                total_saved += item["price"] * item["qty"] - item_total

                st.markdown(f"**{esc(item['name'])}**")
                st.caption(f"📍 {esc(item['brand'])} | {esc(item['event'])}")

                minus_col, num_col, plus_col, del_col = st.columns(4, gap="small")
                with minus_col:
                    if st.button("－", key=f"fc_minus_{key}", use_container_width=True):
                        if st.session_state.cart[key]["qty"] > 1:
                            st.session_state.cart[key]["qty"] -= 1
                        else:
                            del st.session_state.cart[key]
                        st.rerun()
                with num_col:
                    st.markdown(
                        f"<div style='text-align:center;padding-top:8px;font-weight:700;'>{item['qty']}</div>",
                        unsafe_allow_html=True,
                    )
                with plus_col:
                    if st.button("＋", key=f"fc_plus_{key}", use_container_width=True):
                        st.session_state.cart[key]["qty"] += 1
                        st.rerun()
                with del_col:
                    if st.button("🗑", key=f"fc_del_{key}", use_container_width=True):
                        del st.session_state.cart[key]
                        st.rerun()

                render_cart_warning(item)
                st.markdown(f"결제 예상: **{item_total:,}원** (총 {total_received}개)")
                st.caption(f"개당 {unit_price_actual:,}원")
                st.markdown("---")

            st.markdown(
                f"""
                <div style="width:100%;box-sizing:border-box;background:#1e3a5f;border-radius:10px;padding:14px;text-align:center;margin-bottom:8px;">
                    <div style="color:#aaa;font-size:0.8rem;">총 결제 예상금액</div>
                    <div style="color:#fff;font-size:1.5rem;font-weight:900;">{total_price:,}원</div>
                    <div style="color:#4caf50;font-size:0.85rem;margin-top:4px;">💚 {total_saved:,}원 절약 중!</div>
                    <div style="color:#ff6b6b;font-size:0.75rem;margin-top:2px;">※ 행사 적용 실제 결제가 기준</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🗑️ 전체 비우기", use_container_width=True, key="fc_clear_all"):
                st.session_state.cart = {}
                st.rerun()
