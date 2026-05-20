from django.contrib import admin

from .models import (
    BonusClaim,
    Boss,
    BossDamageLog,
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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "level", "title", "xp", "coins", "updated_at")
    search_fields = ("user__username", "display_name")


@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "xp_reward", "coin_reward", "is_active", "ordering")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")


@admin.register(QuestCompletion)
class QuestCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "quest", "date", "completed_at")
    list_filter = ("date", "quest__category")
    search_fields = ("user__username", "quest__name")


@admin.register(BonusClaim)
class BonusClaimAdmin(admin.ModelAdmin):
    list_display = ("user", "bonus_type", "date", "completed_at")
    list_filter = ("bonus_type", "date")


@admin.register(QuickAction)
class QuickActionAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "xp_reward", "coin_reward", "is_active", "ordering")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")


@admin.register(QuickActionLog)
class QuickActionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "created_at")
    list_filter = ("action__category", "created_at")
    search_fields = ("user__username", "action__name")


@admin.register(Boss)
class BossAdmin(admin.ModelAdmin):
    list_display = ("name", "difficulty", "hp", "xp_reward", "coin_reward", "is_active", "reset_weekly")
    list_filter = ("difficulty", "is_active", "reset_weekly")
    search_fields = ("name", "description")


@admin.register(BossProgress)
class BossProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "boss", "damage", "cleared", "week_start", "updated_at")
    list_filter = ("cleared", "week_start")
    search_fields = ("user__username", "boss__name")


@admin.register(GiftFund)
class GiftFundAdmin(admin.ModelAdmin):
    list_display = ("user", "current_amount_million", "target_amount_million", "updated_at")


@admin.register(GiftMilestone)
class GiftMilestoneAdmin(admin.ModelAdmin):
    list_display = ("amount_million", "name", "xp_reward", "coin_reward", "badge_label", "title_reward")


@admin.register(GiftMilestoneUnlock)
class GiftMilestoneUnlockAdmin(admin.ModelAdmin):
    list_display = ("user", "milestone", "unlocked_at")
    search_fields = ("user__username", "milestone__name")


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "cost", "required_level", "allow_repeat", "is_active", "ordering")
    list_filter = ("category", "allow_repeat", "is_active", "required_level")
    search_fields = ("name", "description")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "purchased_at")
    list_filter = ("item__category", "purchased_at")
    search_fields = ("user__username", "item__name")


@admin.register(SmokingLog)
class SmokingLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "cigarettes_count", "daily_limit", "updated_at")
    list_filter = ("date",)
    search_fields = ("user__username",)


@admin.register(BossDamageLog)
class BossDamageLogAdmin(admin.ModelAdmin):
    list_display = ("user", "boss_instance", "damage", "source", "source_name", "created_at")
    list_filter = ("source", "created_at")
    search_fields = ("user__username", "source_name")


@admin.register(MentalCheckIn)
class MentalCheckInAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "energy", "focus", "mood", "motivation", "stress", "control")
    list_filter = ("date",)


@admin.register(Reflection)
class ReflectionAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "updated_at")
    list_filter = ("date",)
    search_fields = ("user__username", "text")


@admin.register(WeeklyArchive)
class WeeklyArchiveAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "week_start",
        "xp_gained",
        "quests_completed",
        "perfect_days",
        "german_sessions",
        "gym_sessions",
        "issues_closed",
        "smoking_limit_days",
    )
    list_filter = ("week_start",)


@admin.register(RewardEvent)
class RewardEventAdmin(admin.ModelAdmin):
    list_display = ("user", "source", "source_key", "xp_delta", "coin_delta", "week_start", "created_at")
    list_filter = ("source", "week_start", "created_at")
    search_fields = ("user__username", "source_key", "note")


@admin.register(WeeklyRun)
class WeeklyRunAdmin(admin.ModelAdmin):
    list_display = ("user", "chapter_name", "week_start", "week_end", "is_active", "generated_at", "closed_at")
    list_filter = ("is_active", "week_start", "chapter_name")
    search_fields = ("user__username", "chapter_name")


@admin.register(WeeklyBossTemplate)
class WeeklyBossTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "difficulty", "category", "xp_reward", "coin_reward", "is_active")
    list_filter = ("difficulty", "category", "is_active")
    search_fields = ("name", "description")


@admin.register(WeeklyBossInstance)
class WeeklyBossInstanceAdmin(admin.ModelAdmin):
    list_display = ("user", "template", "weekly_run", "current_hp", "max_hp", "cleared", "created_at")
    list_filter = ("cleared", "template__difficulty", "weekly_run__week_start")
    search_fields = ("user__username", "template__name")


@admin.register(WeeklyChallengeTemplate)
class WeeklyChallengeTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "xp_reward", "coin_reward", "is_active", "ordering")
    list_filter = ("category", "is_active")
    search_fields = ("title", "description")


@admin.register(WeeklyChallengeInstance)
class WeeklyChallengeInstanceAdmin(admin.ModelAdmin):
    list_display = ("user", "template", "weekly_run", "completed", "completed_at")
    list_filter = ("completed", "weekly_run__week_start", "template__category")
    search_fields = ("user__username", "template__title")


@admin.register(RandomEventTemplate)
class RandomEventTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "rarity", "is_active", "ordering")
    list_filter = ("event_type", "rarity", "is_active")
    search_fields = ("title", "description", "effect_description")


@admin.register(WeeklyRandomEvent)
class WeeklyRandomEventAdmin(admin.ModelAdmin):
    list_display = ("user", "template", "weekly_run", "activated", "created_at")
    list_filter = ("activated", "template__rarity", "weekly_run__week_start")
    search_fields = ("user__username", "template__title")


@admin.register(WeeklyStats)
class WeeklyStatsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "weekly_run",
        "xp_gained",
        "coins_gained",
        "daily_quests_completed",
        "quick_actions_completed",
        "bosses_cleared",
        "created_at",
    )
    list_filter = ("weekly_run__week_start",)
