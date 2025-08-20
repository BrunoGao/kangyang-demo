# 多阶段构建
FROM maven:3.8.4-openjdk-11-slim AS builder

WORKDIR /app

# 复制pom.xml和src目录
COPY pom.xml .
COPY src ./src

# Maven构建
RUN mvn dependency:resolve
RUN mvn clean package -DskipTests

# 运行时镜像
FROM openjdk:11-jre-slim

WORKDIR /app

# 创建非root用户
RUN groupadd -r kangyang && useradd -r -g kangyang kangyang

# 安装curl用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制jar包
COPY --from=builder /app/target/fall-detection-backend-1.0.0.jar app.jar

# 创建日志目录并设置权限
RUN mkdir -p /app/logs && chown -R kangyang:kangyang /app

# 切换到非root用户
USER kangyang

# 设置JVM参数
ENV JAVA_OPTS="-Xmx512m -Xms256m -Dspring.profiles.active=docker"

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

# 启动应用
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]