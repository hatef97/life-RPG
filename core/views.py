from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import GiftAmountForm, LoginForm, MentalCheckInForm, ReflectionForm, SignupForm
from .models import (
    BonusClaim,
    BossDamageLog,
    DailyQuest,
    MentalCheckIn,
    QuestCompletion,
    QuickAction,
    QuickActionLog,
    Reflection,
    SmokingLog,
    WeeklyArchive,
    WeeklyStats,
)
from .selectors import dashboard_context, gift_milestone_rows, profile_resources, shop_item_rows
from .services import (
    adjust_gift_fund,
    adjust_smoking,
    apply_boss_auto_damage,
    claim_daily_bonus,
    claim_quick_action,
    clear_boss,
    complete_daily_quest,
    complete_weekly_challenge,
    compute_weekly_stats,
    deal_boss_damage,
    ensure_profile,
    english_date,
    generate_weekly_archive,
    get_gift_fund,
    get_or_create_current_week,
    get_or_create_smoking_log,
    percent,
    purchase_shop_item,
    save_checkin,
    save_reflection,
    today,
    uncomplete_daily_quest,
    xp_progress,
)


def parse_date(value, fallback=None):
    fallback = fallback or today()
    if not value:
        return fallback
    try:
        return date.fromisoformat(value)
    except ValueError:
        return fallback


def flash_result(request, result):
    level = messages.SUCCESS if result.ok else messages.WARNING
    messages.add_message(request, level, result.message)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        display_name = form.cleaned_data.get("display_name")
        if display_name:
            user.profile.display_name = display_name
            user.profile.save(update_fields=["display_name", "updated_at"])
        login(request, user)
        get_or_create_current_week(user)
        messages.success(request, "اکانت ساخته شد. وارد OS شدی.")
        return redirect("dashboard")
    return render(request, "core/auth.html", {"form": form, "mode": "signup"})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            ensure_profile(user)
            get_or_create_current_week(user)
            messages.success(request, "ورود انجام شد.")
            return redirect("dashboard")
    return render(request, "core/auth.html", {"form": form, "mode": "login"})


def logout_view(request):
    logout(request)
    messages.info(request, "خارج شدی.")
    return redirect("login")


@login_required
def dashboard(request):
    return render(request, "core/dashboard.html", dashboard_context(request.user))


@login_required
def daily_quests(request):
    selected_date = today()
    quests = DailyQuest.objects.filter(is_active=True)
    completed_ids = set(
        QuestCompletion.objects.filter(user=request.user, date=selected_date).values_list("quest_id", flat=True)
    )
    active_count = quests.count()
    completed_count = len(completed_ids)
    rows = [{"quest": quest, "completed": quest.pk in completed_ids} for quest in quests]
    context = {
        "selected_date": selected_date,
        "quest_rows": rows,
        "completed_count": completed_count,
        "active_count": active_count,
        "completion_percent": percent(completed_count, active_count),
        "combo_unlocked": completed_count >= 3,
        "combo_claimed": BonusClaim.objects.filter(
            user=request.user,
            date=selected_date,
            bonus_type=BonusClaim.COMBO,
        ).exists(),
        "perfect_unlocked": active_count > 0 and completed_count == active_count,
        "perfect_claimed": BonusClaim.objects.filter(
            user=request.user,
            date=selected_date,
            bonus_type=BonusClaim.PERFECT_DAY,
        ).exists(),
    }
    return render(request, "core/daily_quests.html", context)


@login_required
@require_POST
def complete_quest_view(request, quest_id):
    result = complete_daily_quest(request.user, quest_id)
    flash_result(request, result)
    if result.ok:
        apply_boss_auto_damage(request.user, "quest", quest_id=quest_id)
    return redirect("daily_quests")


@login_required
@require_POST
def uncomplete_quest_view(request, quest_id):
    flash_result(request, uncomplete_daily_quest(request.user, quest_id))
    return redirect("daily_quests")


@login_required
@require_POST
def claim_daily_bonus_view(request, bonus_type):
    flash_result(request, claim_daily_bonus(request.user, bonus_type))
    return redirect("daily_quests")


@login_required
def quick_actions(request):
    actions = QuickAction.objects.filter(is_active=True)
    logs = QuickActionLog.objects.filter(user=request.user).select_related("action")[:20]
    return render(request, "core/quick_actions.html", {"actions": actions, "logs": logs})


@login_required
@require_POST
def claim_quick_action_view(request, action_id):
    result = claim_quick_action(request.user, action_id)
    flash_result(request, result)
    if result.ok:
        apply_boss_auto_damage(request.user, "quick_action", action_id=action_id)
    return redirect("quick_actions")


@login_required
def boss_arena(request):
    weekly_run = get_or_create_current_week(request.user)
    boss = getattr(weekly_run, "boss_instance", None)
    context = {"weekly_run": weekly_run, "boss": boss}
    if boss:
        context["boss_percent"] = percent(boss.max_hp - boss.current_hp, boss.max_hp)
        context["remaining"] = boss.current_hp
        context["damage_logs"] = BossDamageLog.objects.filter(boss_instance=boss)[:20]
        damage_map = boss.template.category_damage_map or {}
        context["damage_triggers"] = [
            {"category": cat, "damage": dmg} for cat, dmg in damage_map.items()
        ]
    return render(request, "core/boss_arena.html", context)


@login_required
@require_POST
def damage_boss_view(request, instance_id):
    damage = request.POST.get("damage", 20)
    flash_result(request, deal_boss_damage(request.user, instance_id, damage))
    return redirect("boss_arena")


@login_required
@require_POST
def clear_boss_view(request, instance_id):
    flash_result(request, clear_boss(request.user, instance_id))
    return redirect("boss_arena")


@login_required
def weekly_content(request):
    weekly_run = get_or_create_current_week(request.user)
    boss = getattr(weekly_run, "boss_instance", None)
    return render(
        request,
        "core/weekly_content.html",
        {
            "weekly_run": weekly_run,
            "boss": boss,
            "boss_percent": percent(boss.max_hp - boss.current_hp, boss.max_hp) if boss else 0,
            "challenges": weekly_run.challenge_instances.select_related("template"),
            "random_event": getattr(weekly_run, "random_event", None),
        },
    )


@login_required
@require_POST
def complete_weekly_challenge_view(request, instance_id):
    flash_result(request, complete_weekly_challenge(request.user, instance_id))
    return redirect("weekly_content")


@login_required
def gift_fund(request):
    fund = get_gift_fund(request.user)
    context = {
        "fund": fund,
        "fund_percent": percent(fund.current_amount_million, fund.target_amount_million),
        "form": GiftAmountForm(),
        "milestone_rows": gift_milestone_rows(request.user),
    }
    return render(request, "core/gift_fund.html", context)


@login_required
@require_POST
def adjust_gift_fund_view(request):
    form = GiftAmountForm(request.POST)
    if form.is_valid():
        operation = request.POST.get("operation", "add")
        flash_result(request, adjust_gift_fund(request.user, form.cleaned_data["amount"], operation))
    else:
        messages.warning(request, "مبلغ Gift Fund معتبر نیست.")
    return redirect("gift_fund")


@login_required
def shop(request):
    ensure_profile(request.user)
    rows = shop_item_rows(request.user)
    purchases = request.user.purchases.select_related("item")[:12]
    return render(request, "core/shop.html", {"shop_rows": rows, "purchases": purchases})


@login_required
@require_POST
def purchase_shop_item_view(request, item_id):
    flash_result(request, purchase_shop_item(request.user, item_id))
    return redirect("shop")


@login_required
def smoking_tracker(request):
    selected_date = parse_date(request.GET.get("date"))
    log = get_or_create_smoking_log(request.user, selected_date)
    context = {
        "selected_date": selected_date,
        "selected_date_display": english_date(selected_date),
        "log": log,
        "limit": log.daily_limit,
        "over_limit": log.cigarettes_count > log.daily_limit,
        "smoking_percent": min(140, percent(log.cigarettes_count, log.daily_limit)),
    }
    return render(request, "core/smoking_tracker.html", context)


@login_required
@require_POST
def adjust_smoking_view(request):
    selected_date = parse_date(request.POST.get("date"))
    delta = int(request.POST.get("delta", 0))
    log = adjust_smoking(request.user, selected_date, delta)
    if log.cigarettes_count > log.daily_limit:
        messages.error(request, "Limit رد شد. Nicotine Demon Nearby.")
    else:
        messages.success(request, "Smoking log به‌روز شد.")
    return redirect(f"{request.POST.get('next', '/smoking/')}?date={selected_date.isoformat()}")


@login_required
def journal(request):
    selected_date = parse_date(request.GET.get("date"))
    checkin = MentalCheckIn.objects.filter(user=request.user, date=selected_date).first()
    reflection = Reflection.objects.filter(user=request.user, date=selected_date).first()
    checkin_initial = {"date": selected_date}
    if checkin:
        checkin_initial.update(
            {
                "energy": checkin.energy,
                "focus": checkin.focus,
                "mood": checkin.mood,
                "motivation": checkin.motivation,
                "stress": checkin.stress,
                "control": checkin.control,
            }
        )
    else:
        checkin_initial.update({field: 5 for field in ["energy", "focus", "mood", "motivation", "stress", "control"]})
    reflection_initial = {"date": selected_date, "text": reflection.text if reflection else ""}
    return render(
        request,
        "core/journal.html",
        {
            "selected_date": selected_date,
            "selected_date_display": english_date(selected_date),
            "checkin_form": MentalCheckInForm(initial=checkin_initial),
            "reflection_form": ReflectionForm(initial=reflection_initial),
        },
    )


@login_required
@require_POST
def save_checkin_view(request):
    form = MentalCheckInForm(request.POST)
    if form.is_valid():
        checkin = save_checkin(request.user, form)
        messages.success(request, "Mental Check-in ذخیره شد.")
        return redirect(f"/journal/?date={checkin.date.isoformat()}")
    messages.warning(request, "Check-in معتبر نیست.")
    return redirect("journal")


@login_required
@require_POST
def save_reflection_view(request):
    form = ReflectionForm(request.POST)
    if form.is_valid():
        reflection = save_reflection(request.user, form)
        messages.success(request, "Reflection ذخیره شد.")
        return redirect(f"/journal/?date={reflection.date.isoformat()}")
    messages.warning(request, "Reflection معتبر نیست.")
    return redirect("journal")


@login_required
def weekly_review(request):
    weekly_run = get_or_create_current_week(request.user)
    stats = compute_weekly_stats(request.user, weekly_run.week_start)
    current_archive = WeeklyArchive.objects.filter(user=request.user, week_start=stats["week_start"]).first()
    previous_stats = WeeklyStats.objects.filter(user=request.user).exclude(weekly_run=weekly_run).select_related("weekly_run").first()
    profile = ensure_profile(request.user)
    context = {
        "weekly_run": weekly_run,
        "stats": stats,
        "current_archive": current_archive,
        "previous_stats": previous_stats,
        "profile": profile,
        "resources": profile_resources(profile),
        "xp_meta": xp_progress(profile),
    }
    return render(request, "core/weekly_review.html", context)


@login_required
@require_POST
def generate_weekly_archive_view(request):
    weekly_run = get_or_create_current_week(request.user)
    archive = generate_weekly_archive(request.user, weekly_run.week_start)
    messages.success(request, f"Weekly Archive برای هفته {english_date(archive.week_start)} ساخته شد.")
    return redirect("weekly_review")
