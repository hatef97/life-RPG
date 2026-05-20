from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=120, blank=True)
    level = models.PositiveSmallIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=80, default="Lost Starter")
    hp = models.PositiveSmallIntegerField(default=82, validators=[MaxValueValidator(100)])
    stamina = models.PositiveSmallIntegerField(default=72, validators=[MaxValueValidator(100)])
    focus = models.PositiveSmallIntegerField(default=76, validators=[MaxValueValidator(100)])
    momentum = models.PositiveSmallIntegerField(default=64, validators=[MaxValueValidator(100)])
    intelligence = models.PositiveIntegerField(default=12)
    discipline = models.PositiveIntegerField(default=10)
    strength = models.PositiveIntegerField(default=8)
    communication = models.PositiveIntegerField(default=7)
    charisma = models.PositiveIntegerField(default=7)
    builder = models.PositiveIntegerField(default=11)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.get_username()


class DailyQuest(models.Model):
    CATEGORY_CHOICES = [
        ("work", "Work"),
        ("german", "German"),
        ("fitness", "Fitness"),
        ("health", "Health"),
        ("recovery", "Recovery"),
        ("hygiene", "Hygiene"),
        ("home", "Home"),
    ]

    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    xp_reward = models.PositiveIntegerField(default=0)
    coin_reward = models.PositiveIntegerField(default=0)
    attribute_rewards = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="health")
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name


class QuestCompletion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quest_completions")
    quest = models.ForeignKey(DailyQuest, on_delete=models.CASCADE, related_name="completions")
    date = models.DateField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "quest", "date"], name="unique_daily_quest_completion"),
        ]
        ordering = ["-date", "-completed_at"]

    def __str__(self):
        return f"{self.user} - {self.quest} - {self.date}"


class BonusClaim(models.Model):
    COMBO = "combo"
    PERFECT_DAY = "perfect_day"
    BONUS_CHOICES = [
        (COMBO, "Combo Bonus"),
        (PERFECT_DAY, "Perfect Day"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bonus_claims")
    date = models.DateField()
    bonus_type = models.CharField(max_length=30, choices=BONUS_CHOICES)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date", "bonus_type"], name="unique_daily_bonus_claim"),
        ]
        ordering = ["-date", "-completed_at"]

    def __str__(self):
        return f"{self.user} - {self.bonus_type} - {self.date}"


class QuickAction(models.Model):
    CATEGORY_CHOICES = [
        ("work", "Work"),
        ("german", "German"),
        ("fitness", "Fitness"),
        ("health", "Health"),
        ("shipping", "Shipping"),
        ("social", "Social"),
    ]

    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    xp_reward = models.PositiveIntegerField(default=10)
    coin_reward = models.PositiveIntegerField(default=2)
    attribute_rewards = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="work")
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name


class QuickActionLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quick_action_logs")
    action = models.ForeignKey(QuickAction, on_delete=models.CASCADE, related_name="logs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.action}"


class Boss(models.Model):
    DIFFICULTY_CHOICES = [
        ("A", "A Rank"),
        ("S", "S Rank"),
        ("SS", "SS Rank"),
    ]

    name = models.CharField(max_length=160)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="A")
    description = models.TextField(blank=True)
    xp_reward = models.PositiveIntegerField(default=100)
    coin_reward = models.PositiveIntegerField(default=25)
    hp = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    reset_weekly = models.BooleanField(default=True)
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name


class BossProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boss_progress")
    boss = models.ForeignKey(Boss, on_delete=models.CASCADE, related_name="progress")
    damage = models.PositiveIntegerField(default=0)
    cleared = models.BooleanField(default=False)
    week_start = models.DateField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "boss", "week_start"], name="unique_weekly_boss_progress"),
        ]
        ordering = ["boss__ordering"]

    def __str__(self):
        return f"{self.user} - {self.boss} - {self.week_start}"


class GiftFund(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gift_fund")
    current_amount_million = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    target_amount_million = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("50.00"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} gift fund"


class GiftMilestone(models.Model):
    amount_million = models.DecimalField(max_digits=8, decimal_places=2, unique=True)
    name = models.CharField(max_length=120)
    xp_reward = models.PositiveIntegerField(default=75)
    coin_reward = models.PositiveIntegerField(default=20)
    badge_label = models.CharField(max_length=120, blank=True)
    title_reward = models.CharField(max_length=120, blank=True)
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["amount_million"]

    def __str__(self):
        return f"{self.amount_million}M - {self.name}"


class GiftMilestoneUnlock(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gift_milestone_unlocks")
    milestone = models.ForeignKey(GiftMilestone, on_delete=models.CASCADE, related_name="unlocks")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "milestone"], name="unique_gift_milestone_unlock"),
        ]
        ordering = ["-unlocked_at"]

    def __str__(self):
        return f"{self.user} - {self.milestone}"


class ShopItem(models.Model):
    CATEGORY_CHOICES = [
        ("consumable", "Consumable"),
        ("food", "Food"),
        ("recovery", "Recovery"),
        ("style", "Style"),
        ("gear", "Gear"),
        ("experience", "Experience"),
    ]

    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    cost = models.PositiveIntegerField()
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="consumable")
    required_level = models.PositiveSmallIntegerField(default=1)
    allow_repeat = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["ordering", "cost", "name"]

    def __str__(self):
        return self.name


class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name="purchases")
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-purchased_at"]
        indexes = [
            models.Index(fields=["user", "item"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.item}"


class SmokingLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="smoking_logs")
    date = models.DateField()
    cigarettes_count = models.PositiveSmallIntegerField(default=0)
    daily_limit = models.PositiveSmallIntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_daily_smoking_log"),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} - {self.date}: {self.cigarettes_count}"


class MentalCheckIn(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mental_checkins")
    date = models.DateField()
    energy = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    focus = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    mood = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    motivation = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    stress = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    control = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_daily_mental_checkin"),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} - {self.date}"


class Reflection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reflections")
    date = models.DateField()
    text = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_daily_reflection"),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} - {self.date}"


class WeeklyArchive(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_archives")
    week_start = models.DateField()
    xp_gained = models.IntegerField(default=0)
    quests_completed = models.PositiveIntegerField(default=0)
    perfect_days = models.PositiveIntegerField(default=0)
    german_sessions = models.PositiveIntegerField(default=0)
    gym_sessions = models.PositiveIntegerField(default=0)
    issues_closed = models.PositiveIntegerField(default=0)
    smoking_limit_days = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "week_start"], name="unique_weekly_archive"),
        ]
        ordering = ["-week_start"]

    def __str__(self):
        return f"{self.user} - week of {self.week_start}"


class WeeklyRun(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_runs")
    week_start = models.DateField()
    week_end = models.DateField()
    chapter_name = models.CharField(max_length=120)
    generated_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "week_start"], name="unique_weekly_run_per_user_week"),
        ]
        ordering = ["-week_start"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.chapter_name} - {self.week_start}"


class WeeklyBossTemplate(models.Model):
    DIFFICULTY_CHOICES = [
        ("Common", "Common"),
        ("Rare", "Rare"),
        ("Epic", "Epic"),
        ("Legendary", "Legendary"),
    ]

    name = models.CharField(max_length=160)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="Rare")
    description = models.TextField(blank=True)
    objectives = models.JSONField(default=list, blank=True)
    category_damage_map = models.JSONField(default=dict, blank=True)
    xp_reward = models.PositiveIntegerField(default=120)
    coin_reward = models.PositiveIntegerField(default=30)
    attribute_rewards = models.JSONField(default=dict, blank=True)
    category = models.CharField(max_length=60, default="growth")
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name


class WeeklyBossInstance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_boss_instances")
    weekly_run = models.OneToOneField(WeeklyRun, on_delete=models.CASCADE, related_name="boss_instance")
    template = models.ForeignKey(WeeklyBossTemplate, on_delete=models.PROTECT, related_name="instances")
    current_hp = models.PositiveIntegerField()
    max_hp = models.PositiveIntegerField()
    cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-weekly_run__week_start"]

    def __str__(self):
        return f"{self.user} - {self.template} - {self.weekly_run.week_start}"


class BossDamageLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boss_damage_logs")
    boss_instance = models.ForeignKey(WeeklyBossInstance, on_delete=models.CASCADE, related_name="damage_logs")
    damage = models.PositiveIntegerField()
    source = models.CharField(max_length=60)
    source_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -{self.damage} HP via {self.source}"


class WeeklyChallengeTemplate(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=60, default="growth")
    xp_reward = models.PositiveIntegerField(default=50)
    coin_reward = models.PositiveIntegerField(default=12)
    attribute_rewards = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["ordering", "title"]

    def __str__(self):
        return self.title


class WeeklyChallengeInstance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_challenge_instances")
    weekly_run = models.ForeignKey(WeeklyRun, on_delete=models.CASCADE, related_name="challenge_instances")
    template = models.ForeignKey(WeeklyChallengeTemplate, on_delete=models.PROTECT, related_name="instances")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["weekly_run", "template"], name="unique_weekly_challenge_template_per_run"),
        ]
        ordering = ["template__ordering", "template__title"]

    def __str__(self):
        return f"{self.user} - {self.template} - {self.weekly_run.week_start}"


class RandomEventTemplate(models.Model):
    RARITY_CHOICES = [
        ("Common", "Common"),
        ("Rare", "Rare"),
        ("Epic", "Epic"),
        ("Legendary", "Legendary"),
    ]

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=60, default="state")
    effect_description = models.TextField(blank=True)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default="Common")
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["ordering", "title"]

    def __str__(self):
        return self.title


class WeeklyRandomEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_random_events")
    weekly_run = models.OneToOneField(WeeklyRun, on_delete=models.CASCADE, related_name="random_event")
    template = models.ForeignKey(RandomEventTemplate, on_delete=models.PROTECT, related_name="weekly_events")
    activated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.template} - {self.weekly_run.week_start}"


class WeeklyStats(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_stats")
    weekly_run = models.OneToOneField(WeeklyRun, on_delete=models.CASCADE, related_name="stats")
    xp_gained = models.IntegerField(default=0)
    coins_gained = models.IntegerField(default=0)
    daily_quests_completed = models.PositiveIntegerField(default=0)
    perfect_days = models.PositiveIntegerField(default=0)
    quick_actions_completed = models.PositiveIntegerField(default=0)
    german_sessions = models.PositiveIntegerField(default=0)
    gym_sessions = models.PositiveIntegerField(default=0)
    issues_closed = models.PositiveIntegerField(default=0)
    smoking_limit_days = models.PositiveIntegerField(default=0)
    bosses_cleared = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-weekly_run__week_start"]

    def __str__(self):
        return f"{self.user} stats - {self.weekly_run.week_start}"


class RewardEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reward_events")
    source = models.CharField(max_length=60)
    source_key = models.CharField(max_length=180, blank=True)
    xp_delta = models.IntegerField(default=0)
    coin_delta = models.IntegerField(default=0)
    note = models.CharField(max_length=240, blank=True)
    week_start = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "week_start"]),
            models.Index(fields=["source", "source_key"]),
        ]

    def __str__(self):
        return f"{self.user} {self.source}: {self.xp_delta} XP"
