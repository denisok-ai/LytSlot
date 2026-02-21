# npm: сетевые ошибки при установке

## ECONNRESET / network aborted

Если при `npm install` появляется ошибка вида:

```
npm error code ECONNRESET
npm error network aborted
npm error network This is a problem related to network connectivity.
```

### Что сделать

1. **Повторить установку** — часто это временный обрыв соединения:
   ```bash
   cd services/web
   npm install
   ```

2. **Увеличить таймауты и число повторов** (при нестабильном интернете):
   ```bash
   npm config set fetch-retries 5
   npm config set fetch-retry-mintimeout 60000
   npm config set fetch-retry-maxtimeout 120000
   ```
   Затем снова выполнить `npm install`.

3. **Прокси/VPN** — если вы за прокси или VPN, задайте настройки:
   ```bash
   npm config set proxy http://proxy.example.com:8080
   npm config set https-proxy http://proxy.example.com:8080
   ```
   Если прокси не нужен, сбросьте: `npm config delete proxy && npm config delete https-proxy`.

4. **Другой registry** (если блокируют registry.npmjs.org):
   ```bash
   npm config set registry https://registry.npmmirror.com
   ```
   Или временно: `npm install --registry https://registry.npmmirror.com`

---

## Предупреждение про устаревший ESLint 8

Сообщение вида «eslint@8.57.1 is deprecated» при установке в проекте уже исправлено: используется **ESLint 9** и flat config (`eslint.config.mjs`). После успешного `npm install` это предупреждение не должно появляться.
