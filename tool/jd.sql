/*
 Navicat Premium Data Transfer

 Source Server         : TiDB
 Source Server Type    : MySQL
 Source Server Version : 50728 (5.7.28-TiDB-Serverless)
 Source Host           : gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000
 Source Schema         : jd

 Target Server Type    : MySQL
 Target Server Version : 50728 (5.7.28-TiDB-Serverless)
 File Encoding         : 65001

 Date: 14/05/2024 07:11:14
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for jd
-- ----------------------------
DROP TABLE IF EXISTS `jd`;
CREATE TABLE `jd` (
  `id` varchar(255) NOT NULL,
  `url` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `position` varchar(255) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `proxy` tinyint(1) DEFAULT NULL,
  `pay_type` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `guide` varchar(255) DEFAULT NULL,
  `scale` varchar(50) DEFAULT NULL,
  `update_date` date DEFAULT NULL,
  `salary` varchar(100) DEFAULT NULL,
  `experience` varchar(100) DEFAULT NULL,
  `degree` varchar(50) DEFAULT NULL,
  `company` varchar(255) DEFAULT NULL,
  `company_introduce` text DEFAULT NULL,
  `industry` varchar(255) DEFAULT NULL,
  `fund` varchar(255) DEFAULT NULL,
  `res` date DEFAULT NULL,
  `boss` varchar(100) DEFAULT NULL,
  `boss_title` varchar(100) DEFAULT NULL,
  `boss_id` varchar(255) DEFAULT NULL,
  `active` varchar(50) DEFAULT NULL,
  `skill` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `communicated` tinyint(1) DEFAULT NULL,
  `checked_time` datetime DEFAULT NULL,
  `level` varchar(50) DEFAULT NULL,
  `failed_fields` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

SET FOREIGN_KEY_CHECKS = 1;
