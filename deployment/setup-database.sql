-- 康养AI检测系统数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS kangyang 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'kangyang'@'localhost' IDENTIFIED BY '123456';
CREATE USER IF NOT EXISTS 'kangyang'@'%' IDENTIFIED BY '123456';

-- 授权
GRANT ALL PRIVILEGES ON kangyang.* TO 'kangyang'@'localhost';
GRANT ALL PRIVILEGES ON kangyang.* TO 'kangyang'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示创建结果
SHOW DATABASES LIKE 'kangyang';
SELECT User, Host FROM mysql.user WHERE User = 'kangyang';