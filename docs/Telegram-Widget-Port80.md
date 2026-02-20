# Telegram Login Widget и порт 80

Ошибка в браузере:
```text
Framing 'https://oauth.telegram.org/' violates the following Content Security Policy directive: "frame-ancestors http://72.56.117.159"
```

**Причина:** В BotFather вы указываете домен без порта (например `72.56.117.159`). Telegram разрешает встраивать виджет только для origin **http://72.56.117.159** (порт 80). Если приложение открыто по адресу **http://72.56.117.159:3000**, origin другой, и браузер блокирует iframe по CSP.

**Решение:** Отдавать приложение через порт 80 (или 443 для HTTPS). Ниже — вариант с Nginx как обратным прокси.

---

## Nginx: прокси на порт 80

1. Установите Nginx (если ещё не установлен):
   ```bash
   sudo apt update && sudo apt install -y nginx
   ```

2. Создайте конфиг (подставьте свой IP или домен):
   ```bash
   sudo nano /etc/nginx/sites-available/lytslot
   ```

   Содержимое (замените `72.56.117.159` на ваш IP или домен):
   ```nginx
   server {
       listen 80;
       server_name 72.56.117.159;

       # Next.js (веб-кабинет)
       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_cache_bypass $http_upgrade;
       }

       # Опционально: API тоже через тот же домен (например /api-backend -> 8000)
       # location /api-backend/ {
       #     proxy_pass http://127.0.0.1:8000/;
       #     proxy_set_header Host $host;
       #     proxy_set_header X-Real-IP $remote_addr;
       #     proxy_set_header X-Forwarded-Proto $scheme;
       # }
   }
   ```

3. Включите сайт и перезапустите Nginx:
   ```bash
   sudo ln -sf /etc/nginx/sites-available/lytslot /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```

4. Откройте в браузере: **http://72.56.117.159** (без `:3000`).  
   В BotFather домен уже указан как `72.56.117.159` — origin совпадёт, виджет «Log in with Telegram» должен загружаться.

5. В **services/web/.env.local** на сервере укажите URL без порта:
   ```bash
   NEXT_PUBLIC_APP_URL=http://72.56.117.159
   ```
   Перезапустите `npm run dev` в `services/web`.

---

## Если пока не ставите Nginx

Входите через **режим разработки**: откройте **http://72.56.117.159:3000/login?dev=1**, введите **123456789** и нажмите «Войти для разработки». Тогда виджет Telegram не используется.
