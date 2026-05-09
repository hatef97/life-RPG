from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import (
    DailyQuest,
    GiftMilestone,
    QuickAction,
    RandomEventTemplate,
    ShopItem,
    WeeklyBossTemplate,
    WeeklyChallengeTemplate,
)


class Command(BaseCommand):
    help = "Seed fixed Life RPG content, shop rewards, weekly templates, and gift milestones."

    def handle(self, *args, **options):
        self.seed_daily_quests()
        self.seed_quick_actions()
        self.seed_shop_items()
        self.seed_weekly_boss_templates()
        self.seed_weekly_challenge_templates()
        self.seed_random_event_templates()
        self.seed_gift_milestones()
        self.stdout.write(self.style.SUCCESS("Default RPG data seeded."))

    def seed_daily_quests(self):
        quests = [
            ("👨‍💻 2h Fittec Deep Work", "دو ساعت کار عمیق روی Fittec بدون حواس‌پرتی.", 50, 18, {"builder": 3, "discipline": 2}, "work", 10),
            ("🇩🇪 German 90m", "جلسه کامل آلمانی برای مسیر B2.", 60, 15, {"intelligence": 3, "communication": 2}, "german", 20),
            ("🍽️ Hit Calorie Target", "کالری و پروتئین هدف امروز زده شود.", 40, 10, {"strength": 2, "discipline": 1}, "fitness", 30),
            ("🚬 ≤15 Cigarettes", "کنترل نیکوتین و نگه داشتن سقف روزانه.", 40, 12, {"discipline": 3}, "health", 40),
            ("😴 Sleep Before 2AM", "خاموشی قبل از ۲ بامداد برای بازسازی.", 30, 8, {"discipline": 1}, "recovery", 50),
            ("🧴 Skincare x2", "روتین صبح و شب.", 20, 5, {"charisma": 1}, "hygiene", 60),
            ("🪥 Brush Teeth x2", "دو بار مسواک کامل.", 15, 4, {"charisma": 1}, "hygiene", 70),
            ("🐈 Clean Dobby Litter", "محیط تمیز برای Dobby.", 20, 5, {"discipline": 1}, "home", 80),
        ]
        for name, description, xp, coins, attrs, category, ordering in quests:
            DailyQuest.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "xp_reward": xp,
                    "coin_reward": coins,
                    "attribute_rewards": attrs,
                    "category": category,
                    "ordering": ordering,
                    "is_active": True,
                },
            )

    def seed_quick_actions(self):
        actions = [
            ("30m Deep Work", "یک اسپرینت کوتاه اما واقعی.", 20, 6, {"builder": 1, "discipline": 1}, "work", 10),
            ("Linear Issue Closed", "یک Issue واقعی بسته شد.", 35, 10, {"builder": 2}, "work", 20),
            ("Important Bug Fixed", "Bug مهم بدون بدهی جدید بسته شد.", 45, 12, {"builder": 2, "intelligence": 1}, "work", 30),
            ("Deploy / Release Task", "یک Release یا Deploy تمیز.", 50, 14, {"builder": 3}, "shipping", 40),
            ("German Speaking 20m", "تمرین صحبت کردن با صدای بلند.", 25, 7, {"communication": 2}, "german", 50),
            ("Listening / Shadowing", "شنیدن فعال و Shadowing.", 20, 5, {"intelligence": 1, "communication": 1}, "german", 60),
            ("90m Gym Session", "تمرین کامل باشگاه.", 55, 14, {"strength": 3, "discipline": 1}, "fitness", 70),
            ("Physique Progress Photo", "ثبت داده واقعی برای مسیر فیزیک.", 15, 4, {"discipline": 1}, "fitness", 80),
            ("Project Outreach", "پیام یا ارتباط ارزشمند برای پروژه.", 30, 8, {"communication": 2, "charisma": 1}, "social", 90),
            ("No Indoor Smoking", "یک تصمیم محیطی درست.", 25, 6, {"discipline": 2}, "health", 100),
        ]
        for name, description, xp, coins, attrs, category, ordering in actions:
            QuickAction.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "xp_reward": xp,
                    "coin_reward": coins,
                    "attribute_rewards": attrs,
                    "category": category,
                    "ordering": ordering,
                    "is_active": True,
                },
            )

    def seed_shop_items(self):
        items = [
            ("☕ Coffee Reward", "یک قهوه بدون حس گناه؛ پاداش کوچک برای ریتم خوب.", 120, "consumable", 1, True, 10),
            ("🍔 Favorite Meal", "یک وعده محبوب بعد از اجرای واقعی برنامه.", 250, "food", 1, True, 20),
            ("🎬 Chill Night", "یک شب استراحت کنترل‌شده بدون خراب کردن فردا.", 400, "recovery", 2, True, 30),
            ("👕 Clothing Item", "یک آیتم پوشاک برای Arc جدید.", 1200, "style", 3, False, 40),
            ("👟 Shoes Unlock", "ارتقای جدی ظاهر و حرکت.", 3000, "style", 4, False, 50),
            ("🌫️ Perfume Reward", "پاداش هویتی برای حضور بهتر.", 3500, "style", 4, False, 60),
            ("🎧 Gadget", "ابزار یا گجت مفید، نه خرید بی‌هدف.", 5000, "gear", 5, False, 70),
            ("✈️ Experience Reward", "تجربه ارزشمند برای مرحله بعد.", 8000, "experience", 6, False, 80),
        ]
        for name, description, cost, category, required_level, allow_repeat, ordering in items:
            ShopItem.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "cost": cost,
                    "category": category,
                    "required_level": required_level,
                    "allow_repeat": allow_repeat,
                    "is_active": True,
                    "ordering": ordering,
                },
            )

    def seed_weekly_boss_templates(self):
        bosses = [
            (
                "🚀 Launch Beast",
                "Epic",
                "بستن کارهای Launch و خروج از حالت تعلیق.",
                ["25h Deep Work", "10 Linear Issues", "7h German", "3 Gym Sessions", "Smoking average under limit"],
                180,
                45,
                {"builder": 5, "discipline": 2},
                "shipping",
                10,
            ),
            (
                "🇩🇪 Sprachjäger",
                "Rare",
                "شکار B2 با تمرین‌های سنگین آلمانی.",
                ["7 Speaking Sessions", "5 Immersion Sessions", "0 skipped German days"],
                140,
                32,
                {"communication": 4, "intelligence": 3},
                "german",
                20,
            ),
            (
                "🍖 Mass Builder",
                "Rare",
                "کالری، تمرین و استمرار فیزیکی.",
                ["3 Gym Sessions", "10 Calorie Targets", "+0.5kg Weekly Weight"],
                130,
                30,
                {"strength": 5, "discipline": 2},
                "fitness",
                30,
            ),
            (
                "🌙 Night Hunter",
                "Epic",
                "شکستن چرخه شب‌زنده‌داری و کنترل نیکوتین.",
                ["No Chain Smoking", "7 Days Under Cigarette Limit", "No Indoor Smoking"],
                160,
                38,
                {"discipline": 5},
                "recovery",
                40,
            ),
            (
                "🐍 Backend Forge",
                "Epic",
                "ساختن Backend تمیز و قابل اتکا.",
                ["4h Django Backend", "3 Linear Issues", "1 Clean Commit", "No Scrolling During Sprint"],
                220,
                60,
                {"builder": 6, "intelligence": 3},
                "backend",
                50,
            ),
        ]
        for name, difficulty, description, objectives, xp, coins, attrs, category, ordering in bosses:
            WeeklyBossTemplate.objects.update_or_create(
                name=name,
                defaults={
                    "difficulty": difficulty,
                    "description": description,
                    "objectives": objectives,
                    "xp_reward": xp,
                    "coin_reward": coins,
                    "attribute_rewards": attrs,
                    "category": category,
                    "is_active": True,
                    "ordering": ordering,
                },
            )

    def seed_weekly_challenge_templates(self):
        challenges = [
            ("🧴 Clean Identity Week", "skincare x2 for 5 days", "hygiene", 70, 18, {"charisma": 2}, 10),
            ("🪥 Discipline Basics", "brush teeth x2 for 7 days", "hygiene", 65, 16, {"discipline": 2}, 20),
            ("🐈 Dobby Care Week", "clean Dobby litter daily", "home", 60, 14, {"discipline": 2}, 30),
            ("🇩🇪 Speaking Pressure", "5 speaking sessions", "german", 90, 24, {"communication": 3}, 40),
            ("💪 Bulk Protocol", "calorie target 6 days", "fitness", 90, 24, {"strength": 3}, 50),
            ("🚬 Control Week", "no indoor smoking 5 days", "health", 85, 22, {"discipline": 3}, 60),
            ("👨‍💻 Builder Sprint", "15h deep work", "work", 110, 30, {"builder": 4}, 70),
            ("😴 Recovery Week", "sleep before 2AM for 5 days", "recovery", 75, 20, {"discipline": 2}, 80),
        ]
        for title, description, category, xp, coins, attrs, ordering in challenges:
            WeeklyChallengeTemplate.objects.update_or_create(
                title=title,
                defaults={
                    "description": description,
                    "category": category,
                    "xp_reward": xp,
                    "coin_reward": coins,
                    "attribute_rewards": attrs,
                    "is_active": True,
                    "ordering": ordering,
                },
            )

    def seed_random_event_templates(self):
        events = [
            ("⚡ Locked In State", "ذهن آماده اجرای سنگین است.", "buff", "+10% focus discipline for the week", "Rare", 10),
            ("🌧️ Low Energy Day", "هفته انرژی پایین دارد؛ تصمیم‌های کوچک مهم‌ترند.", "warning", "Keep quests lighter but never zero.", "Common", 20),
            ("🧠 Focus Window", "یک بازه طلایی برای Deep Work پیدا می‌شود.", "buff", "Prioritize one long sprint.", "Rare", 30),
            ("🚬 Nicotine Demon Nearby", "وسوسه نیکوتین نزدیک است.", "threat", "Smoking tracker becomes priority.", "Epic", 40),
            ("🌌 Alignment Surge", "چند محور زندگی هم‌زمان هماهنگ شده‌اند.", "buff", "Perfect Day is worth protecting.", "Epic", 50),
            ("💀 Chaos Warning", "هفته مستعد شلوغی و فرار ذهنی است.", "warning", "Reduce noise and keep daily anchors.", "Rare", 60),
            ("🎁 Rare Loot Drop", "یک فرصت پاداش واقعی باز شده است.", "loot", "Shop reward feels cheaper psychologically.", "Legendary", 70),
            ("🧘 Recovery Window", "بدن و ذهن درخواست بازسازی دارند.", "recovery", "Sleep and recovery quests become priority.", "Common", 80),
        ]
        for title, description, event_type, effect, rarity, ordering in events:
            RandomEventTemplate.objects.update_or_create(
                title=title,
                defaults={
                    "description": description,
                    "event_type": event_type,
                    "effect_description": effect,
                    "rarity": rarity,
                    "is_active": True,
                    "ordering": ordering,
                },
            )

    def seed_gift_milestones(self):
        milestones = [
            (5, "First Sacrifice"),
            (10, "Momentum Saver"),
            (15, "Serious Intent"),
            (20, "Premium Arc"),
            (25, "Locked In"),
            (30, "Rebuild Provider"),
            (35, "Mission Focused"),
            (40, "Main Character Energy"),
            (45, "Almost There"),
            (50, "Birthday Mission Complete"),
        ]
        for index, (amount, name) in enumerate(milestones, start=1):
            GiftMilestone.objects.update_or_create(
                amount_million=Decimal(amount),
                defaults={
                    "name": name,
                    "xp_reward": 50 + index * 10,
                    "coin_reward": 10 + index * 2,
                    "badge_label": f"{amount}M Gift Badge",
                    "title_reward": name if amount in {25, 50} else "",
                    "ordering": index * 10,
                },
            )
