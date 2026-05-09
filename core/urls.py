from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),
    path("quests/", views.daily_quests, name="daily_quests"),
    path("quests/<int:quest_id>/complete/", views.complete_quest_view, name="complete_quest"),
    path("quests/<int:quest_id>/uncomplete/", views.uncomplete_quest_view, name="uncomplete_quest"),
    path("quests/bonus/<str:bonus_type>/", views.claim_daily_bonus_view, name="claim_daily_bonus"),
    path("quick-actions/", views.quick_actions, name="quick_actions"),
    path("quick-actions/<int:action_id>/claim/", views.claim_quick_action_view, name="claim_quick_action"),
    path("boss-arena/", views.boss_arena, name="boss_arena"),
    path("boss-arena/<int:instance_id>/damage/", views.damage_boss_view, name="damage_boss"),
    path("boss-arena/<int:instance_id>/clear/", views.clear_boss_view, name="clear_boss"),
    path("weekly-content/", views.weekly_content, name="weekly_content"),
    path("weekly-content/challenge/<int:instance_id>/complete/", views.complete_weekly_challenge_view, name="complete_weekly_challenge"),
    path("gift-fund/", views.gift_fund, name="gift_fund"),
    path("gift-fund/adjust/", views.adjust_gift_fund_view, name="adjust_gift_fund"),
    path("shop/", views.shop, name="shop"),
    path("shop/<int:item_id>/purchase/", views.purchase_shop_item_view, name="purchase_shop_item"),
    path("smoking/", views.smoking_tracker, name="smoking_tracker"),
    path("smoking/adjust/", views.adjust_smoking_view, name="adjust_smoking"),
    path("journal/", views.journal, name="journal"),
    path("journal/checkin/", views.save_checkin_view, name="save_checkin"),
    path("journal/reflection/", views.save_reflection_view, name="save_reflection"),
    path("weekly-review/", views.weekly_review, name="weekly_review"),
    path("weekly-review/generate/", views.generate_weekly_archive_view, name="generate_weekly_archive"),
]
