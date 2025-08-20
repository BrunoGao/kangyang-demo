FROM openjdk:11-jre-slim

WORKDIR /app

# 复制jar包
COPY target/fall-detection-backend-1.0.0.jar app.jar

# 暴露端口
EXPOSE 8080

# 启动应用
ENTRYPOINT ["java", "-jar", "app.jar"]