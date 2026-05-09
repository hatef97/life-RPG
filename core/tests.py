from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from .models import (
    BonusClaim,
    DailyQuest,
    GiftMilestone,
    GiftMilestoneUnlock,
    Purchase,
    QuestCompletion,
    RandomEventTemplate,
    RewardEvent,
    ShopItem,
    WeeklyBossInstance,
    WeeklyBossTemplate,
    WeeklyChallengeInstance,
    WeeklyChallengeTemplate,
    WeeklyRandomEvent,
    WeeklyStats,
)
from .services import (
    adjust_gift_fund,
    claim_daily_bonus,
    clear_boss,
    complete_daily_quest,
    get_or_create_current_week,
    purchase_shop_item,
    today,
    uncomplete_daily_quest,
)


class RewardMechanicsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hatef", password="pass12345")
        self.quest = DailyQuest.objects.create(
            name="Deep Work",
            xp_reward=50,
            coin_reward=18,
            attribute_rewards={"builder": 2},
            is_active=True,
        )
        self.seed_weekly_templates()

    def seed_weekly_templates(self):
        WeeklyBossTemplate.objects.create(name="Launch Beast", difficulty="Epic", xp_reward=120, coin_reward=30)
        WeeklyChallengeTemplate.objects.create(title="Builder Sprint")
        WeeklyChallengeTemplate.objects.create(title="Control Week")
        RandomEventTemplate.objects.create(title="Locked In")

    def test_daily_quest_awards_only_once_per_day(self):
        first = complete_daily_quest(self.user, self.quest.id)
        second = complete_daily_quest(self.user, self.quest.id)
        self.user.profile.refresh_from_db()

        self.assertTrue(first.ok)
        self.assertFalse(second.ok)
        self.assertEqual(self.user.profile.xp, 50)
        self.assertEqual(QuestCompletion.objects.count(), 1)
        self.assertEqual(RewardEvent.objects.filter(source="daily_quest").count(), 1)

    def test_uncomplete_and_recomplete_is_net_single_reward(self):
        complete_daily_quest(self.user, self.quest.id)
        uncomplete_daily_quest(self.user, self.quest.id)
        complete_daily_quest(self.user, self.quest.id)
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.profile.xp, 50)
        self.assertEqual(self.user.profile.coins, 18)
        self.assertEqual(QuestCompletion.objects.count(), 1)

    def test_combo_and_perfect_bonus_are_claimed_once(self):
        DailyQuest.objects.bulk_create(
            [
                DailyQuest(name="German", xp_reward=10, coin_reward=1, is_active=True),
                DailyQuest(name="Calories", xp_reward=10, coin_reward=1, is_active=True),
            ]
        )
        for quest in DailyQuest.objects.all():
            complete_daily_quest(self.user, quest.id)

        combo = claim_daily_bonus(self.user, BonusClaim.COMBO)
        combo_again = claim_daily_bonus(self.user, BonusClaim.COMBO)
        perfect = claim_daily_bonus(self.user, BonusClaim.PERFECT_DAY)
        self.user.profile.refresh_from_db()

        self.assertTrue(combo.ok)
        self.assertFalse(combo_again.ok)
        self.assertTrue(perfect.ok)
        self.assertEqual(BonusClaim.objects.count(), 2)
        self.assertEqual(self.user.profile.xp, 50 + 10 + 10 + 30 + 100)

    def test_weekly_boss_clear_awards_once(self):
        weekly_run = get_or_create_current_week(self.user, date(2026, 5, 4))
        boss = weekly_run.boss_instance

        first = clear_boss(self.user, boss.id)
        second = clear_boss(self.user, boss.id)
        self.user.profile.refresh_from_db()

        self.assertTrue(first.ok)
        self.assertFalse(second.ok)
        self.assertEqual(self.user.profile.xp, boss.template.xp_reward)
        self.assertEqual(RewardEvent.objects.filter(source="weekly_boss_clear").count(), 1)

    def test_gift_milestone_unlocks_once(self):
        GiftMilestone.objects.create(amount_million=Decimal("5"), name="First Sacrifice", xp_reward=60, coin_reward=12)

        adjust_gift_fund(self.user, Decimal("5"), "add")
        adjust_gift_fund(self.user, Decimal("1"), "add")
        self.user.profile.refresh_from_db()

        self.assertEqual(GiftMilestoneUnlock.objects.count(), 1)
        self.assertEqual(self.user.profile.xp, 60)
        self.assertEqual(self.user.profile.coins, 12)

    def test_shop_purchase_spends_coins_and_blocks_duplicate_non_repeatable(self):
        item = ShopItem.objects.create(name="Gadget", cost=100, required_level=1, allow_repeat=False)
        self.user.profile.coins = 150
        self.user.profile.save(update_fields=["coins"])

        first = purchase_shop_item(self.user, item.id)
        second = purchase_shop_item(self.user, item.id)
        self.user.profile.refresh_from_db()

        self.assertTrue(first.ok)
        self.assertFalse(second.ok)
        self.assertEqual(self.user.profile.coins, 50)
        self.assertEqual(Purchase.objects.count(), 1)

    def test_today_helper_returns_date(self):
        self.assertTrue(hasattr(today(), "isoformat"))


class WeeklyRunTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="weekly", password="pass12345")
        self.profile = self.user.profile
        self.profile.xp = 900
        self.profile.coins = 300
        self.profile.builder = 19
        self.profile.save()
        self.seed_templates()

    def seed_templates(self):
        WeeklyBossTemplate.objects.create(name="Launch Beast", difficulty="Epic", ordering=1)
        WeeklyBossTemplate.objects.create(name="Backend Forge", difficulty="Epic", ordering=2)
        WeeklyChallengeTemplate.objects.create(title="Builder Sprint", ordering=1)
        WeeklyChallengeTemplate.objects.create(title="Control Week", ordering=2)
        WeeklyChallengeTemplate.objects.create(title="Recovery Week", ordering=3)
        RandomEventTemplate.objects.create(title="Locked In", ordering=1)
        RandomEventTemplate.objects.create(title="Focus Window", ordering=2)

    def test_same_week_does_not_regenerate_content(self):
        first = get_or_create_current_week(self.user, date(2026, 5, 4))
        boss_id = first.boss_instance.template_id
        challenge_ids = list(first.challenge_instances.order_by("id").values_list("template_id", flat=True))
        event_id = first.random_event.template_id

        second = get_or_create_current_week(self.user, date(2026, 5, 9))

        self.assertEqual(first.id, second.id)
        self.assertEqual(second.boss_instance.template_id, boss_id)
        self.assertEqual(list(second.challenge_instances.order_by("id").values_list("template_id", flat=True)), challenge_ids)
        self.assertEqual(second.random_event.template_id, event_id)
        self.assertEqual(WeeklyBossInstance.objects.count(), 1)
        self.assertEqual(WeeklyChallengeInstance.objects.count(), 2)
        self.assertEqual(WeeklyRandomEvent.objects.count(), 1)

    def test_new_week_archives_old_week(self):
        old_run = get_or_create_current_week(self.user, date(2026, 5, 4))
        complete_daily_quest(self.user, DailyQuest.objects.create(name="Quest", xp_reward=10, coin_reward=2).id, date(2026, 5, 4))

        new_run = get_or_create_current_week(self.user, date(2026, 5, 11))
        old_run.refresh_from_db()

        self.assertNotEqual(old_run.id, new_run.id)
        self.assertFalse(old_run.is_active)
        self.assertIsNotNone(old_run.closed_at)
        self.assertTrue(new_run.is_active)
        self.assertTrue(WeeklyStats.objects.filter(weekly_run=old_run).exists())

    def test_new_week_generates_one_boss_two_challenges_one_event(self):
        run = get_or_create_current_week(self.user, date(2026, 5, 4))

        self.assertTrue(hasattr(run, "boss_instance"))
        self.assertEqual(run.challenge_instances.count(), 2)
        self.assertTrue(hasattr(run, "random_event"))

    def test_week_rollover_does_not_reset_long_term_progress(self):
        get_or_create_current_week(self.user, date(2026, 5, 4))
        get_or_create_current_week(self.user, date(2026, 5, 11))
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.profile.xp, 900)
        self.assertEqual(self.user.profile.coins, 300)
        self.assertEqual(self.user.profile.builder, 19)

    def test_weekly_content_remains_stable_after_refresh(self):
        run = get_or_create_current_week(self.user, date(2026, 5, 4))
        snapshot = (
            run.boss_instance.template_id,
            tuple(run.challenge_instances.order_by("id").values_list("template_id", flat=True)),
            run.random_event.template_id,
        )

        for _ in range(3):
            refreshed = get_or_create_current_week(self.user, date(2026, 5, 5))
            current = (
                refreshed.boss_instance.template_id,
                tuple(refreshed.challenge_instances.order_by("id").values_list("template_id", flat=True)),
                refreshed.random_event.template_id,
            )
            self.assertEqual(current, snapshot)
