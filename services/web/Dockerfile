FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM node:20-alpine AS builder
WORKDIR /app
ARG API_BACKEND_URL=http://api:8000
# Передайте --build-arg CACHEBUST=$(date +%s) чтобы принудительно пересобрать COPY (обход кэша)
ARG CACHEBUST
RUN echo "build ${CACHEBUST:-none}"
ENV API_BACKEND_URL=$API_BACKEND_URL
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Если в проекте нет public/, создаём пустую — иначе COPY в runner падает
RUN mkdir -p public && npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
