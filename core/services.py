from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from .models import (
    BonusClaim,
    Boss,
    BossProgress,
    DailyQuest,
    GiftFund,
    GiftMilestone,
    GiftMilestoneUnlock,
    MentalCheckIn,
    Profile,
    Purchase,
    QuestCompletion,
    QuickAction,
    QuickActionLog,
    RandomEventTemplate,
    Reflection,
    RewardEvent,
    ShopItem,
    SmokingLog,
    WeeklyArchive,
    WeeklyBossInstance,
    WeeklyBossTemplate,
    WeeklyChallengeInstance,
    WeeklyChallengeTemplate,
    WeeklyRandomEvent,
    WeeklyRun,
    WeeklyStats,
)


ATTRIBUTE_FIELDS = [
    "intelligence",
    "discipline",
    "strength",
    "communication",
    "charisma",
    "builder",
]

LEVEL_THRESHOLDS = {
    1: 0,
    2: 800,
    3: 1800,
    4: 3200,
    5: 5000,
    6: 7500,
    7: 10500,
    8: 14000,
    9: 18000,
    10: 23000,
}

LEVEL_TITLES = {
    1: "Lost Starter",
    2: "Momentum Builder",
    3: "Discipline Mode",
    4: "Deep Work Operator",
    5: "Builder Mindset",
    6: "Launch Beast",
    7: "B2 Warrior",
    8: "High Performance Mode",
    9: "Rebuild Era",
    10: "Main Character Arc",
}

BONUS_REWARDS = {
    BonusClaim.COMBO: {"xp": 30, "coins": 10, "label": "Combo Bonus"},
    BonusClaim.PERFECT_DAY: {"xp": 100, "coins": 30, "label": "Perfect Day"},
}

BOSS_HP_BY_DIFFICULTY = {
    "Common": 90,
    "Rare": 120,
    "Epic": 160,
    "Legendary": 220,
}


@dataclass(frozen=True)
class OperationResult:
    ok: bool
    message: str


def today() -> date:
    return timezone.localdate()


def get_current_week_range(current_day: date | None = None) -> tuple[date, date]:
    current_day = current_day or today()
    week_start = current_day - timedelta(days=current_day.weekday())
    return week_start, week_start + timedelta(days=6)


def get_week_start(day: date | None = None) -> date:
    return get_current_week_range(day)[0]


def english_date(value: date | None) -> str:
    if value is None:
        return ""
    if hasattr(value, "date"):
        value = value.date()
    return f"{value.strftime('%A, %B')} {value.day}, {value.year}"


def percent(value, total) -> int:
    if not total:
        return 0
    return max(0, min(100, int((float(value) / float(total)) * 100)))


def ensure_profile(user) -> Profile:
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"display_name": user.get_full_name() or user.get_username()},
    )
    sync_profile_level(profile, save=True)
    return profile


def sync_profile_level(profile: Profile, save: bool = False) -> Profile:
    level = 1
    for candidate, threshold in LEVEL_THRESHOLDS.items():
        if profile.xp >= threshold:
            level = candidate
    profile.level = level
    profile.title = LEVEL_TITLES[level]
    if save:
        profile.save(update_fields=["level", "title", "updated_at"])
    return profile


def xp_progress(profile: Profile) -> dict:
    level = profile.level
    current_floor = LEVEL_THRESHOLDS[level]
    next_level = min(level + 1, max(LEVEL_THRESHOLDS))
    next_floor = LEVEL_THRESHOLDS[next_level]
    if level == max(LEVEL_THRESHOLDS):
        return {
            "current_floor": current_floor,
            "next_floor": current_floor,
            "remaining": 0,
            "percent": 100,
            "next_level": None,
        }
    earned_in_level = profile.xp - current_floor
    needed = next_floor - current_floor
    return {
        "current_floor": current_floor,
        "next_floor": next_floor,
        "remaining": max(0, next_floor - profile.xp),
        "percent": percent(earned_in_level, needed),
        "next_level": next_level,
    }


@transaction.atomic
def award_reward(
    user,
    *,
    xp: int = 0,
    coins: int = 0,
    attribute_rewards: dict | None = None,
    source: str,
    source_key: str = "",
    note: str = "",
    event_date: date | None = None,
) -> Profile:
    profile = Profile.objects.select_for_update().get(user=user)
    profile.xp = max(0, profile.xp + int(xp))
    profile.coins = max(0, profile.coins + int(coins))
    for field, delta in (attribute_rewards or {}).items():
        if field in ATTRIBUTE_FIELDS:
            setattr(profile, field, max(0, getattr(profile, field) + int(delta)))
    sync_profile_level(profile)
    profile.save()

    if xp or coins:
        RewardEvent.objects.create(
            user=user,
            source=source,
            source_key=source_key,
            xp_delta=int(xp),
            coin_delta=int(coins),
            note=note[:240],
            week_start=get_week_start(event_date),
        )
    return profile


def get_chapter_name_for_user(user, week_start: date) -> str:
    first_run = WeeklyRun.objects.filter(user=user).order_by("week_start").first()
    if first_run:
        week_number = max(1, ((week_start - first_run.week_start).days // 7) + 1)
    else:
        week_number = 1

    if week_number <= 2:
        return "The Awakening"
    if week_number <= 6:
        return "The Grind"
    if week_number <= 11:
        return "The Transformation"
    return "The Reveal"


def _boss_hp_for_template(template: WeeklyBossTemplate) -> int:
    return BOSS_HP_BY_DIFFICULTY.get(template.difficulty, 120)


def _active_boss_templates_without_previous(user, week_start: date):
    templates = list(WeeklyBossTemplate.objects.filter(is_active=True))
    if len(templates) <= 1:
        return templates

    previous = (
        WeeklyBossInstance.objects.filter(user=user, weekly_run__week_start__lt=week_start)
        .select_related("template", "weekly_run")
        .order_by("-weekly_run__week_start")
        .first()
    )
    if not previous:
        return templates
    filtered = [template for template in templates if template.pk != previous.template_id]
    return filtered or templates


def generate_weekly_content(user, weekly_run: WeeklyRun) -> None:
    # Content is stored as instances; refreshes read these rows and never re-randomize.
    if not hasattr(weekly_run, "boss_instance"):
        boss_templates = _active_boss_templates_without_previous(user, weekly_run.week_start)
        if boss_templates:
            template = random.choice(boss_templates)
            max_hp = _boss_hp_for_template(template)
            WeeklyBossInstance.objects.create(
                user=user,
                weekly_run=weekly_run,
                template=template,
                current_hp=max_hp,
                max_hp=max_hp,
            )

    if weekly_run.challenge_instances.count() < 2:
        existing_ids = set(weekly_run.challenge_instances.values_list("template_id", flat=True))
        templates = list(WeeklyChallengeTemplate.objects.filter(is_active=True).exclude(pk__in=existing_ids))
        random.shuffle(templates)
        for template in templates[: max(0, 2 - weekly_run.challenge_instances.count())]:
            WeeklyChallengeInstance.objects.create(user=user, weekly_run=weekly_run, template=template)

    if not hasattr(weekly_run, "random_event"):
        templates = list(RandomEventTemplate.objects.filter(is_active=True))
        if templates:
            WeeklyRandomEvent.objects.create(
                user=user,
                weekly_run=weekly_run,
                template=random.choice(templates),
                activated=True,
            )


def compute_weekly_stats(user, week_start: date | None = None) -> dict:
    week_start = week_start or get_week_start()
    week_end = week_start + timedelta(days=6)
    reward_qs = RewardEvent.objects.filter(user=user, week_start=week_start)
    reward_totals = reward_qs.aggregate(xp=Sum("xp_delta"), coins=Sum("coin_delta"))

    return {
        "week_start": week_start,
        "week_end": week_end,
        "xp_gained": reward_totals["xp"] or 0,
        "coins_gained": reward_totals["coins"] or 0,
        "daily_quests_completed": QuestCompletion.objects.filter(user=user, date__range=(week_start, week_end)).count(),
        "quests_completed": QuestCompletion.objects.filter(user=user, date__range=(week_start, week_end)).count(),
        "perfect_days": BonusClaim.objects.filter(
            user=user,
            date__range=(week_start, week_end),
            bonus_type=BonusClaim.PERFECT_DAY,
        ).count(),
        "quick_actions_completed": QuickActionLog.objects.filter(
            user=user,
            created_at__date__range=(week_start, week_end),
        ).count(),
        "german_sessions": QuestCompletion.objects.filter(
            user=user,
            date__range=(week_start, week_end),
            quest__category="german",
        ).count()
        + QuickActionLog.objects.filter(
            user=user,
            created_at__date__range=(week_start, week_end),
            action__category="german",
        ).count(),
        "gym_sessions": QuickActionLog.objects.filter(
            user=user,
            created_at__date__range=(week_start, week_end),
            action__category="fitness",
        ).count(),
        "issues_closed": QuickActionLog.objects.filter(
            Q(action__name__icontains="Issue") | Q(action__name__icontains="Bug") | Q(action__name__icontains="Linear"),
            user=user,
            created_at__date__range=(week_start, week_end),
        ).count(),
        "smoking_limit_days": SmokingLog.objects.filter(
            user=user,
            date__range=(week_start, week_end),
            cigarettes_count__lte=15,
        ).count(),
        "bosses_cleared": WeeklyBossInstance.objects.filter(
            user=user,
            weekly_run__week_start=week_start,
            cleared=True,
        ).count(),
    }


def archive_week(weekly_run: WeeklyRun) -> WeeklyStats:
    stats = compute_weekly_stats(weekly_run.user, weekly_run.week_start)
    weekly_stats, _ = WeeklyStats.objects.update_or_create(
        user=weekly_run.user,
        weekly_run=weekly_run,
        defaults={
            "xp_gained": stats["xp_gained"],
            "coins_gained": stats["coins_gained"],
            "daily_quests_completed": stats["daily_quests_completed"],
            "perfect_days": stats["perfect_days"],
            "quick_actions_completed": stats["quick_actions_completed"],
            "german_sessions": stats["german_sessions"],
            "gym_sessions": stats["gym_sessions"],
            "issues_closed": stats["issues_closed"],
            "smoking_limit_days": stats["smoking_limit_days"],
            "bosses_cleared": stats["bosses_cleared"],
        },
    )
    generate_weekly_archive(weekly_run.user, weekly_run.week_start)
    return weekly_stats


@transaction.atomic
def get_or_create_current_week(user, current_day: date | None = None) -> WeeklyRun:
    week_start, week_end = get_current_week_range(current_day)
    active = WeeklyRun.objects.select_for_update().filter(user=user, is_active=True).order_by("-week_start").first()

    if active and active.week_start == week_start:
        generate_weekly_content(user, active)
        return active

    if active and active.week_start != week_start:
        archive_week(active)
        active.is_active = False
        active.closed_at = timezone.now()
        active.save(update_fields=["is_active", "closed_at"])

    weekly_run, created = WeeklyRun.objects.get_or_create(
        user=user,
        week_start=week_start,
        defaults={
            "week_end": week_end,
            "chapter_name": get_chapter_name_for_user(user, week_start),
            "is_active": True,
            "generated_at": timezone.now(),
        },
    )

    if not weekly_run.is_active:
        weekly_run.is_active = True
        weekly_run.closed_at = None
        weekly_run.save(update_fields=["is_active", "closed_at"])

    WeeklyRun.objects.filter(user=user).exclude(pk=weekly_run.pk).update(is_active=False)

    if created or not hasattr(weekly_run, "boss_instance") or weekly_run.challenge_instances.count() < 2 or not hasattr(weekly_run, "random_event"):
        generate_weekly_content(user, weekly_run)

    return weekly_run


@transaction.atomic
def complete_daily_quest(user, quest_id: int, completion_date: date | None = None) -> OperationResult:
    completion_date = completion_date or today()
    quest = DailyQuest.objects.select_for_update().get(pk=quest_id, is_active=True)
    _, created = QuestCompletion.objects.get_or_create(user=user, quest=quest, date=completion_date)
    if not created:
        return OperationResult(False, "این Quest امروز قبلا کامل شده و دوباره XP نمی‌دهد.")

    award_reward(
        user,
        xp=quest.xp_reward,
        coins=quest.coin_reward,
        attribute_rewards=quest.attribute_rewards,
        source="daily_quest",
        source_key=f"{quest.pk}:{completion_date.isoformat()}",
        note=quest.name,
        event_date=completion_date,
    )
    return OperationResult(True, f"{quest.name} کامل شد. +{quest.xp_reward} XP")


@transaction.atomic
def uncomplete_daily_quest(user, quest_id: int, completion_date: date | None = None) -> OperationResult:
    completion_date = completion_date or today()
    quest = DailyQuest.objects.get(pk=quest_id)
    deleted, _ = QuestCompletion.objects.filter(user=user, quest=quest, date=completion_date).delete()
    if not deleted:
        return OperationResult(False, "برای امروز چیزی برای برگشت دادن وجود ندارد.")

    reversed_attrs = {key: -int(value) for key, value in quest.attribute_rewards.items()}
    award_reward(
        user,
        xp=-quest.xp_reward,
        coins=-quest.coin_reward,
        attribute_rewards=reversed_attrs,
        source="daily_quest_reversal",
        source_key=f"{quest.pk}:{completion_date.isoformat()}",
        note=f"Undo {quest.name}",
        event_date=completion_date,
    )
    return OperationResult(True, f"{quest.name} از امروز برداشته شد و پاداشش برگشت خورد.")


@transaction.atomic
def claim_daily_bonus(user, bonus_type: str, claim_date: date | None = None) -> OperationResult:
    claim_date = claim_date or today()
    active_count = DailyQuest.objects.filter(is_active=True).count()
    completed_count = QuestCompletion.objects.filter(user=user, date=claim_date, quest__is_active=True).count()

    if bonus_type == BonusClaim.COMBO and completed_count < 3:
        return OperationResult(False, "Combo بعد از ۳ Quest روزانه باز می‌شود.")
    if bonus_type == BonusClaim.PERFECT_DAY and (active_count == 0 or completed_count < active_count):
        return OperationResult(False, "Perfect Day فقط وقتی همه Questها کامل باشند فعال می‌شود.")
    if bonus_type not in BONUS_REWARDS:
        return OperationResult(False, "Bonus نامعتبر است.")

    _, created = BonusClaim.objects.get_or_create(user=user, date=claim_date, bonus_type=bonus_type)
    if not created:
        return OperationResult(False, "این Bonus برای امروز قبلا گرفته شده است.")

    reward = BONUS_REWARDS[bonus_type]
    award_reward(
        user,
        xp=reward["xp"],
        coins=reward["coins"],
        source="daily_bonus",
        source_key=f"{bonus_type}:{claim_date.isoformat()}",
        note=reward["label"],
        event_date=claim_date,
    )
    return OperationResult(True, f"{reward['label']} فعال شد. +{reward['xp']} XP")


@transaction.atomic
def claim_quick_action(user, action_id: int) -> OperationResult:
    action = QuickAction.objects.get(pk=action_id, is_active=True)
    log = QuickActionLog.objects.create(user=user, action=action)
    award_reward(
        user,
        xp=action.xp_reward,
        coins=action.coin_reward,
        attribute_rewards=action.attribute_rewards,
        source="quick_action",
        source_key=str(log.pk),
        note=action.name,
    )
    return OperationResult(True, f"{action.name} ثبت شد. +{action.xp_reward} XP")


def get_boss_progress(user, boss: Boss, week_start: date | None = None) -> BossProgress:
    week_start = week_start or get_week_start()
    progress, _ = BossProgress.objects.get_or_create(user=user, boss=boss, week_start=week_start)
    return progress


@transaction.atomic
def deal_boss_damage(user, instance_id: int, damage: int = 20) -> OperationResult:
    instance = (
        WeeklyBossInstance.objects.select_for_update()
        .select_related("template", "weekly_run")
        .get(pk=instance_id, user=user)
    )
    if instance.cleared:
        return OperationResult(False, "این Boss برای این هفته Clear شده است.")

    damage = max(1, int(damage))
    instance.current_hp = max(0, instance.current_hp - damage)
    cleared_now = instance.current_hp == 0
    if cleared_now:
        instance.cleared = True
    instance.save(update_fields=["current_hp", "cleared"])

    if cleared_now:
        template = instance.template
        award_reward(
            user,
            xp=template.xp_reward,
            coins=template.coin_reward,
            attribute_rewards=template.attribute_rewards,
            source="weekly_boss_clear",
            source_key=f"{instance.pk}:{instance.weekly_run.week_start.isoformat()}",
            note=template.name,
            event_date=instance.weekly_run.week_start,
        )
        return OperationResult(True, f"{template.name} Clear شد. +{template.xp_reward} XP")
    return OperationResult(True, f"{damage} Damage وارد شد.")


def clear_boss(user, instance_id: int) -> OperationResult:
    instance = WeeklyBossInstance.objects.get(pk=instance_id, user=user)
    return deal_boss_damage(user, instance_id, max(1, instance.current_hp))


@transaction.atomic
def complete_weekly_challenge(user, instance_id: int) -> OperationResult:
    instance = (
        WeeklyChallengeInstance.objects.select_for_update()
        .select_related("template", "weekly_run")
        .get(pk=instance_id, user=user)
    )
    if instance.completed:
        return OperationResult(False, "این Challenge قبلا کامل شده است.")
    instance.completed = True
    instance.completed_at = timezone.now()
    instance.save(update_fields=["completed", "completed_at"])
    template = instance.template
    award_reward(
        user,
        xp=template.xp_reward,
        coins=template.coin_reward,
        attribute_rewards=template.attribute_rewards,
        source="weekly_challenge",
        source_key=f"{instance.pk}:{instance.weekly_run.week_start.isoformat()}",
        note=template.title,
        event_date=instance.weekly_run.week_start,
    )
    return OperationResult(True, f"{template.title} کامل شد. +{template.xp_reward} XP")


def get_gift_fund(user) -> GiftFund:
    fund, _ = GiftFund.objects.get_or_create(user=user)
    return fund


@transaction.atomic
def adjust_gift_fund(user, amount, operation: str) -> OperationResult:
    try:
        parsed = Decimal(str(amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return OperationResult(False, "عدد وارد شده معتبر نیست.")

    if parsed <= 0:
        return OperationResult(False, "مبلغ باید بیشتر از صفر باشد.")

    fund = GiftFund.objects.select_for_update().get_or_create(user=user)[0]
    if operation == "remove":
        fund.current_amount_million = max(Decimal("0.00"), fund.current_amount_million - parsed)
        verb = "کم شد"
    else:
        fund.current_amount_million = min(fund.target_amount_million, fund.current_amount_million + parsed)
        verb = "اضافه شد"
    fund.save(update_fields=["current_amount_million", "updated_at"])
    unlocked = unlock_available_gift_milestones(user, fund)
    extra = f" {unlocked} Milestone جدید باز شد." if unlocked else ""
    return OperationResult(True, f"{parsed}M {verb}.{extra}")


def unlock_available_gift_milestones(user, fund: GiftFund) -> int:
    unlocked_count = 0
    milestones = GiftMilestone.objects.filter(amount_million__lte=fund.current_amount_million)
    for milestone in milestones:
        _, created = GiftMilestoneUnlock.objects.get_or_create(user=user, milestone=milestone)
        if created:
            unlocked_count += 1
            award_reward(
                user,
                xp=milestone.xp_reward,
                coins=milestone.coin_reward,
                source="gift_milestone",
                source_key=str(milestone.pk),
                note=milestone.name,
            )
    return unlocked_count


@transaction.atomic
def purchase_shop_item(user, item_id: int) -> OperationResult:
    item = ShopItem.objects.get(pk=item_id, is_active=True)
    profile = Profile.objects.select_for_update().get(user=user)

    if profile.level < item.required_level:
        return OperationResult(False, f"برای این Reward باید Level {item.required_level} باشی.")
    if not item.allow_repeat and Purchase.objects.filter(user=user, item=item).exists():
        return OperationResult(False, "این Reward قبلا Unlock شده است.")
    if profile.coins < item.cost:
        return OperationResult(False, "Coins کافی نداری.")

    profile.coins -= item.cost
    profile.save(update_fields=["coins", "updated_at"])
    purchase = Purchase.objects.create(user=user, item=item)
    RewardEvent.objects.create(
        user=user,
        source="shop_purchase",
        source_key=str(purchase.pk),
        xp_delta=0,
        coin_delta=-item.cost,
        note=item.name,
        week_start=get_week_start(),
    )
    return OperationResult(True, f"{item.name} از Merchant Shop Unlock شد.")


@transaction.atomic
def adjust_smoking(user, selected_date: date, delta: int) -> SmokingLog:
    log = SmokingLog.objects.select_for_update().get_or_create(user=user, date=selected_date)[0]
    log.cigarettes_count = max(0, log.cigarettes_count + int(delta))
    log.save(update_fields=["cigarettes_count", "updated_at"])
    return log


def save_checkin(user, form) -> MentalCheckIn:
    selected_date = form.cleaned_data["date"]
    defaults = {field: form.cleaned_data[field] for field in ["energy", "focus", "mood", "motivation", "stress", "control"]}
    checkin, _ = MentalCheckIn.objects.update_or_create(user=user, date=selected_date, defaults=defaults)
    return checkin


def save_reflection(user, form) -> Reflection:
    selected_date = form.cleaned_data["date"]
    reflection, _ = Reflection.objects.update_or_create(
        user=user,
        date=selected_date,
        defaults={"text": form.cleaned_data["text"]},
    )
    return reflection


def generate_weekly_archive(user, week_start: date | None = None) -> WeeklyArchive:
    stats = compute_weekly_stats(user, week_start)
    summary = (
        f"Week {english_date(stats['week_start'])} to {english_date(stats['week_end'])}: "
        f"{stats['xp_gained']} XP, {stats['daily_quests_completed']} Quest, "
        f"{stats['perfect_days']} Perfect Day, {stats['german_sessions']} German sessions."
    )
    archive, _ = WeeklyArchive.objects.update_or_create(
        user=user,
        week_start=stats["week_start"],
        defaults={
            "xp_gained": stats["xp_gained"],
            "quests_completed": stats["daily_quests_completed"],
            "perfect_days": stats["perfect_days"],
            "german_sessions": stats["german_sessions"],
            "gym_sessions": stats["gym_sessions"],
            "issues_closed": stats["issues_closed"],
            "smoking_limit_days": stats["smoking_limit_days"],
            "summary": summary,
        },
    )
    return archive


def create_demo_user_if_empty(username: str = "hatef"):
    User = get_user_model()
    if User.objects.exists():
        return None
    user = User.objects.create_user(username=username, password="changeme123")
    ensure_profile(user)
    return user
