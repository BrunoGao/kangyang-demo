# 康养AI检测系统 - MySQL数据库镜像
FROM mysql:8.0

# 设置环境变量
ENV MYSQL_ROOT_PASSWORD=kangyang123
ENV MYSQL_DATABASE=kangyang_db
ENV MYSQL_USER=kangyang_user  
ENV MYSQL_PASSWORD=kangyang_pass

# 复制初始化SQL脚本
COPY init-db.sql /docker-entrypoint-initdb.d/

# 复制MySQL配置
COPY my.cnf /etc/mysql/conf.d/

# 设置字符集
ENV LC_ALL=C.UTF-8
ENV MYSQL_CHARSET=utf8mb4
ENV MYSQL_COLLATION=utf8mb4_unicode_ci

# 暴露端口
EXPOSE 3306

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD mysqladmin ping -h 127.0.0.1 -u root -pkangyang123 || exit 1