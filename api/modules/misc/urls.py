# from django.conf.urls import url
from django.urls import path

from api.modules.misc import views

urlpatterns = \
    [
        path("untis/timetable", views.get_untis_timetable),
        path("services/discord-bot/restart", views.restart_discord_bot_service),
        path("services/self/restart", views.restart_self),
        path("steammarket/itemprice", views.get_price_from_steam_market),
        path("telegrambot/sendMessage", views.send_telegram_message_to_me),
    ]
