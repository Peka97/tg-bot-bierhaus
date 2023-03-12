Description=BH Telegram Bot

[Service]
User=service
WorkingDirectory=/home/service/tg-bot-bierhaus/main
Environment="PATH=/home/service/tg-bot-bierhaus/venv/bin"
ExecStart=/home/service/tg-bot-bierhaus/venv/bin/python main.py --start
ExecStop=/home/service/tg-bot-bierhaus/venv/bin/python main.py --stop
ExecReload=/home/service/tg-bot-bierhaus/venv/bin/python main.py --restart
TimeoutSec=30
Restart=always
