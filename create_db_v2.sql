-- ====================================================
-- Script tạo database student_risk_v2
-- Chạy 1 lần trong MySQL để tạo database mới
-- KHÔNG xóa student_risk_mgmt cũ
-- ====================================================

CREATE DATABASE IF NOT EXISTS student_risk_v2
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE student_risk_v2;

-- Thêm tài khoản admin mặc định sau khi backend tạo bảng
-- (Chạy sau khi đã khởi động backend lần đầu và bảng đã được tạo)
-- INSERT INTO taikhoan (username, password, role) VALUES ('admin', 'admin123', 'admin');
