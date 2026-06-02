"""카테고리 통제 어휘(taxonomy) — D52.

문제(C2): DOM_SPEC·CONSOLIDATE·TC_DESIGN이 `category_major`를 자유 서술하여
같은 도메인이 수백 종으로 파편화됨(실측 436종). 특히 인증 도메인이
"User Management"/"Authentication"/"Account Management" 등으로 분열되어
로그인 편중이 과장되고, Stage 1 dedup이 "다른 대분류=다른 기능"으로 오판함.

해소:
  1) (주 기제) 프롬프트에 고정 목록을 주입해 LLM이 목록 중 선택하도록 강제.
  2) (안전망) coerce_major()로 목록 밖 값을 동의어 규칙으로 보정. 매칭 실패 시
     원본 유지(정보 손실 0) + unknown 샘플 기록 → 어휘 보강 근거.

원칙: 대분류(major)만 통제. 중분류·소분류(leaf)는 그대로 → 시험 커버리지 손실 없음.
"""
from __future__ import annotations

TAXONOMY_VERSION = "v1"

# 고정 대분류 12종 (웹 일반 + ISO 25023 친화, 한국어 고정)
TAXONOMY: list[str] = [
    "회원·인증",       # 로그인/로그아웃/계정/회원가입/프로필 — 분열되던 인증 도메인 통합
    "게시판·콘텐츠",   # 게시글/댓글/커뮤니티/에디터/콘텐츠
    "검색·필터",       # 검색/필터/정렬
    "네비게이션·메뉴", # 메뉴/링크/헤더/푸터/사이드바/레이아웃/이동
    "UI·접근성",       # UI 컨트롤/사용성/접근성/반응형/표시 설정
    "결제·쇼핑",       # 장바구니/주문/결제/상품/쿠폰/위시리스트
    "폼·입력검증",     # 폼/입력/검증/제출
    "알림·고객지원",   # 알림/공지/문의/FAQ/고객지원
    "관리자",          # 관리자/운영
    "정보표시·정책",   # 정보 표시/약관/정책/통계/개인정보
    "설정·환경",       # 환경설정/개인화/디바이스 설정
    "기타",            # 분류 불가 fallback
]
TAXONOMY_SET = set(TAXONOMY)

# 동의어 규칙 — (canonical, [트리거 키워드]) 우선순위 순서대로 평가.
# 키워드는 소문자 부분일치. 충돌(예: "user interface" vs "user account")을 피하려
# 더 구체적·중요한 도메인을 앞에 둔다. 인증 도메인을 최우선(사용자 핵심 불만).
_RULES: list[tuple[str, list[str]]] = [
    ("회원·인증", [
        "login", "logout", "log in", "log out", "sign in", "sign out", "signin", "signout",
        "authentication", "auth", "session", "password", "credential", "identity",
        "account", "member", "register", "registration", "sign up", "signup", "profile",
        "my page", "mypage", "my-page", "access control", "security",
        # "user ..." 도메인은 인증으로 (단 "user interface"는 UI 규칙에서 처리 — 'interface' 미포함)
        "user management", "user account", "user profile", "user personalization",
        "user communication", "user engagement", "user assistance", "user support",
        "user info", "user center",
        "로그인", "로그아웃", "인증", "세션", "비밀번호", "계정", "회원", "가입",
        "프로필", "마이페이지", "탈퇴", "로그",
    ]),
    ("결제·쇼핑", [
        "shopping", "shop", "cart", "wishlist", "checkout", "order", "payment", "pay ",
        "commerce", "coupon", "product", "catalog", "promotion", "loyalty", "reward",
        "points", "discount",
        "쇼핑", "장바구니", "결제", "주문", "상품", "쿠폰", "위시리스트", "위시",
        "카트", "포인트", "할인", "적립",
    ]),
    ("검색·필터", [
        "search", "filter", "sort", "ranking", "discovery", "retrieval",
        "검색", "필터", "정렬", "찾기",
    ]),
    ("게시판·콘텐츠", [
        "board", "bbs", "post", "comment", "community", "editor", "article", "content",
        "writing", "authoring", "reading", "browsing",
        "게시판", "게시글", "게시물", "댓글", "글쓰기", "글 작성", "콘텐츠",
        "커뮤니티", "작성", "에디터", "글 ", "읽기",
    ]),
    ("알림·고객지원", [
        "notification", "notice", "inquiry", "faq", "support", "customer", "qna", "q&a",
        "messaging", "communication",
        "알림", "공지", "문의", "고객지원", "고객", "쪽지", "메시지",
    ]),
    ("관리자", [
        "admin", "administration", "관리자", "운영",
    ]),
    ("UI·접근성", [
        "accessibility", "usability", "responsive", "device", "typography", "readability",
        "user interface", "interface", "ui ", "ui/", "ui:", "ux", "display", "panel",
        "layout",  # layout은 네비보다 UI로
        "접근성", "사용성", "반응형", "디바이스", "표시", "가독성",
        "사용자 인터페이스", "사용자인터페이스", "레이아웃", "패널",
    ]),
    ("정보표시·정책", [
        "information", "info", "legal", "policy", "terms", "privacy", "statistics",
        "analytics", "metrics", "trust",
        "정보", "정책", "약관", "통계", "개인정보", "법적", "안내",
    ]),
    ("설정·환경", [
        "settings", "setting", "preference", "configuration", "config", "personalization",
        "customization", "localization",
        "설정", "환경", "개인화", "맞춤",
    ]),
    ("폼·입력검증", [
        "form", "input", "validation", "submission", "submit",
        "폼", "입력", "검증", "제출", "양식",
    ]),
    ("네비게이션·메뉴", [
        "navigation", "navigaton", "navigaiton", "nav", "menu", "link", "header",
        "footer", "sidebar", "breadcrumb", "site", "page", "web",
        "네비", "메뉴", "탐색", "이동", "헤더", "푸터", "링크", "사이트", "홈",
    ]),
    ("기타", [
        "기타", "other", "misc", "etc", "utility", "utilities", "general", "common",
        "platform", "system", "meta",
        # LLM이 ISO 품질특성명을 대분류로 오용한 경우(도메인 아님) → 기타로 정규화.
        # 근본 해소는 프롬프트의 통제 어휘 주입(NEW run). 여기선 legacy 데이터 보정.
        "functional suitability", "functionality", "기능 적합성", "기능적합성",
        "suitability",
    ]),
]


def coerce_major(name: str) -> tuple[str, str]:
    """대분류명을 통제 어휘로 보정.

    Returns:
        (canonical, status) — status ∈ {"canonical", "coerced", "unknown"}.
        매칭 실패(unknown) 시 원본을 그대로 돌려준다(정보 손실 0).
    """
    raw = (name or "").strip()
    if not raw:
        return "기타", "coerced"
    if raw in TAXONOMY_SET:
        return raw, "canonical"
    low = raw.lower()
    for canonical, keywords in _RULES:
        for kw in keywords:
            if kw and kw in low:
                return canonical, "coerced"
    return raw, "unknown"
