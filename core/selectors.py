from .models import (
    BonusClaim,
    DailyQuest,
    GiftMilestone,
    Purchase,
    QuestCompletion,
    ShopItem,
    SmokingLog,
    WeeklyBossInstance,
)
from .services import (
    english_date,
    ensure_profile,
    get_gift_fund,
    get_or_create_current_week,
    percent,
    today,
    xp_progress,
)


def _boss_overall_percent_selector(boss) -> int:
    if not boss:
        return 0
    objectives = boss.template.objectives or []
    if not objectives:
        return 100 if boss.cleared else 0
    total_target = sum(int(o.get("target", 1)) for o in objectives)
    total_current = sum(
        min(int(boss.objective_progress.get(o["id"], 0)), int(o.get("target", 1)))
        for o in objectives
    )
    return int(total_current * 100 / total_target) if total_target else 0


ATTRIBUTE_LABELS = {
    "intelligence": "Intelligence",
    "discipline": "Discipline",
    "strength": "Strength",
    "communication": "Communication",
    "charisma": "Charisma",
    "builder": "Builder",
}


def profile_resources(profile):
    return [
        {"label": "HP", "value": profile.hp, "percent": profile.hp, "tone": "danger"},
        {"label": "Stamina", "value": profile.stamina, "percent": profile.stamina, "tone": "success"},
        {"label": "Focus", "value": profile.focus, "percent": profile.focus, "tone": "violet"},
        {"label": "Momentum", "value": profile.momentum, "percent": profile.momentum, "tone": "gold"},
    ]


def profile_attributes(profile):
    rows = []
    for field, label in ATTRIBUTE_LABELS.items():
        value = getattr(profile, field)
        rows.append({"label": label, "value": value, "percent": min(100, value), "tone": "blue"})
    return rows


def current_state(user, selected_date=None):
    selected_date = selected_date or today()
    profile = ensure_profile(user)
    completed = QuestCompletion.objects.filter(user=user, date=selected_date, quest__is_active=True).count()
    active_count = DailyQuest.objects.filter(is_active=True).count()
    smoking = SmokingLog.objects.filter(user=user, date=selected_date).first()

    if smoking and smoking.cigarettes_count > smoking.daily_limit:
        return {"label": "Nicotine Demon Nearby", "tone": "danger", "copy": "Limit شکسته شده؛ امروز باید کنترل برگردد."}
    if active_count and completed == active_count:
        return {"label": "Alignment", "tone": "success", "copy": "همه محورهای روز روی ریل هستند."}
    if completed >= 3 or profile.momentum >= 75:
        return {"label": "Momentum", "tone": "gold", "copy": "ریتم ساخته شده؛ ادامه بده."}
    return {"label": "Normal", "tone": "blue", "copy": "روز هنوز قابل شکل دادن است."}


def daily_quest_preview(user):
    selected_date = today()
    completed_ids = set(QuestCompletion.objects.filter(user=user, date=selected_date).values_list("quest_id", flat=True))
    return [{"quest": quest, "completed": quest.pk in completed_ids} for quest in DailyQuest.objects.filter(is_active=True)[:4]]


def achievement_preview(user):
    selected_date = today()
    active_count = DailyQuest.objects.filter(is_active=True).count()
    completed = QuestCompletion.objects.filter(user=user, date=selected_date, quest__is_active=True).count()
    combo_claimed = BonusClaim.objects.filter(user=user, date=selected_date, bonus_type=BonusClaim.COMBO).exists()
    perfect_claimed = BonusClaim.objects.filter(user=user, date=selected_date, bonus_type=BonusClaim.PERFECT_DAY).exists()
    boss_total = WeeklyBossInstance.objects.filter(user=user, weekly_run__is_active=True).count()
    boss_cleared = WeeklyBossInstance.objects.filter(user=user, weekly_run__is_active=True, cleared=True).count()
    gift_fund = get_gift_fund(user)

    return [
        {
            "title": "Daily Combo",
            "meta": f"{completed}/3 Quest",
            "percent": percent(min(completed, 3), 3),
            "unlocked": combo_claimed,
        },
        {
            "title": "Perfect Day",
            "meta": f"{completed}/{active_count} Quest",
            "percent": percent(completed, active_count),
            "unlocked": perfect_claimed,
        },
        {
            "title": "Boss Hunter",
            "meta": f"{boss_cleared}/{boss_total} Weekly Boss",
            "percent": percent(boss_cleared, boss_total),
            "unlocked": boss_total > 0 and boss_cleared == boss_total,
        },
        {
            "title": "Gift Mission",
            "meta": f"{gift_fund.current_amount_million}M / {gift_fund.target_amount_million}M",
            "percent": percent(gift_fund.current_amount_million, gift_fund.target_amount_million),
            "unlocked": gift_fund.current_amount_million >= gift_fund.target_amount_million,
        },
    ]


def shop_item_rows(user, limit=None):
    purchased_ids = set(Purchase.objects.filter(user=user).values_list("item_id", flat=True))
    items = ShopItem.objects.filter(is_active=True)
    if limit:
        items = items[:limit]
    return [
        {
            "item": item,
            "unlocked": item.pk in purchased_ids,
            "can_buy": user.profile.level >= item.required_level and user.profile.coins >= item.cost,
        }
        for item in items
    ]


def smoking_status(user):
    log = SmokingLog.objects.filter(user=user, date=today()).first()
    count = log.cigarettes_count if log else 0
    limit = log.daily_limit if log else 10
    return {
        "count": count,
        "limit": limit,
        "over_limit": count > limit,
        "percent": min(140, percent(count, limit)),
    }


def dashboard_context(user):
    profile = ensure_profile(user)
    weekly_run = get_or_create_current_week(user)
    weekly_boss = getattr(weekly_run, "boss_instance", None)
    fund = get_gift_fund(user)
    return {
        "today_display": english_date(today()),
        "profile": profile,
        "xp_meta": xp_progress(profile),
        "resources": profile_resources(profile),
        "attributes": profile_attributes(profile),
        "state": current_state(user),
        "achievements": achievement_preview(user),
        "weekly_run": weekly_run,
        "weekly_boss": weekly_boss,
        "weekly_boss_percent": _boss_overall_percent_selector(weekly_boss),
        "weekly_challenges": weekly_run.challenge_instances.select_related("template"),
        "weekly_event": getattr(weekly_run, "random_event", None),
        "daily_quest_preview": daily_quest_preview(user),
        "gift_fund": fund,
        "gift_percent": percent(fund.current_amount_million, fund.target_amount_million),
        "shop_preview": shop_item_rows(user, limit=4),
        "smoking_status": smoking_status(user),
    }


def gift_milestone_rows(user):
    fund = get_gift_fund(user)
    unlocked_ids = set(user.gift_milestone_unlocks.values_list("milestone_id", flat=True))
    rows = []
    for milestone in GiftMilestone.objects.all():
        rows.append(
            {
                "milestone": milestone,
                "unlocked": milestone.pk in unlocked_ids,
                "reached": fund.current_amount_million >= milestone.amount_million,
                "percent": percent(fund.current_amount_million, milestone.amount_million),
            }
        )
    return rows
