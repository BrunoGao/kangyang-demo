# 管理平台前端 Dockerfile
FROM node:22-alpine as build

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package.json ./

# 配置npm使用阿里源并安装依赖
RUN npm config set registry https://registry.npmmirror.com/ && \
    npm cache clean --force && \
    rm -rf node_modules package-lock.json && \
    npm install && \
    npm rebuild esbuild

# 复制源代码
COPY . .

# 显示package.json确认配置
RUN cat package.json

# 修复vite bin文件路径
RUN sed -i "s|import('../dist/node/cli.js')|import('../vite/dist/node/cli.js')|g" node_modules/.bin/vite

# 强制重新安装esbuild以匹配架构
RUN npm uninstall esbuild && npm install esbuild@latest

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost || exit 1

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]