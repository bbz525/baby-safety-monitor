FROM node:20-alpine AS builder
WORKDIR /app

# 先安装依赖，利用缓存
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# 拷贝源码并构建
COPY . .
ENV VITE_API_BASE=http://localhost:8080
RUN npm run build

# 运行时镜像，使用 serve 启动静态站点
FROM node:20-alpine AS runner
WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 4173
CMD ["serve", "-s", "dist", "-l", "4173"]
