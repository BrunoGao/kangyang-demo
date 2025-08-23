# 管理平台后端 Dockerfile
FROM openjdk:17-jdk-slim AS builder

# 设置工作目录
WORKDIR /app

# 配置阿里云APT源加速
RUN sed -i 's@http://deb.debian.org@http://mirrors.aliyun.com@g' /etc/apt/sources.list && \
    sed -i 's@http://security.debian.org@http://mirrors.aliyun.com@g' /etc/apt/sources.list

# 安装Maven
RUN apt-get update && apt-get install -y maven && rm -rf /var/lib/apt/lists/*

# 复制Maven构建文件和配置
COPY pom.xml .
COPY settings.xml /root/.m2/settings.xml

# 复制源代码
COPY src src

# 构建应用（使用阿里云Maven镜像）
RUN mvn clean package -DskipTests

# 运行时镜像
FROM openjdk:17-jdk-slim

# 配置阿里云APT源加速
RUN sed -i 's@http://deb.debian.org@http://mirrors.aliyun.com@g' /etc/apt/sources.list && \
    sed -i 's@http://security.debian.org@http://mirrors.aliyun.com@g' /etc/apt/sources.list

# 安装必要的工具
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 从构建阶段复制jar文件
COPY --from=builder /app/target/fall-detection-backend-1.0.0.jar app.jar

# 健康检查 - 使用简单的端口检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["java", "-jar", "app.jar"]