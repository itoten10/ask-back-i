-- ASK 探究学習システム Phase1 マイグレーション
-- 投稿・評価システムの基礎テーブル作成
-- 作成日: 2025-12-08

-- ==============================================
-- 1. evaluation_periods（評価期間マスタ）
-- ==============================================
CREATE TABLE IF NOT EXISTS evaluation_periods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================
-- 2. non_cog_abilities（非認知能力マスタ）
-- ==============================================
CREATE TABLE IF NOT EXISTS non_cog_abilities (
    id TINYINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================
-- 3. ability_rubrics（能力ルーブリック）
-- ==============================================
CREATE TABLE IF NOT EXISTS ability_rubrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ability_id TINYINT NOT NULL,
    level TINYINT NOT NULL,
    title VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    coefficient DECIMAL(3,1) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ability_id) REFERENCES non_cog_abilities(id),
    UNIQUE (ability_id, level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================
-- 4. ability_score_bands（パーセンタイル帯設定）
-- ==============================================
CREATE TABLE IF NOT EXISTS ability_score_bands (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ability_id TINYINT NULL,
    grade TINYINT NULL,
    band_order TINYINT NOT NULL,
    signal_color ENUM('red','yellow','green') NOT NULL,
    band_label VARCHAR(50) NOT NULL,
    percentile_min DECIMAL(5,2) NOT NULL,
    percentile_max DECIMAL(5,2),
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE (ability_id, grade, band_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================
-- 5. posts（投稿）
-- ==============================================
CREATE TABLE IF NOT EXISTS posts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    problem TEXT NOT NULL,
    content_1 TEXT NOT NULL,
    content_2 TEXT,
    content_3 TEXT,
    question_state_change_type ENUM('none','deepened','changed') NOT NULL DEFAULT 'none',
    phase_label VARCHAR(50) NOT NULL,
    ai_raw_label JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    KEY idx_posts_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================
-- 6. user_period_posts_cache（期間別投稿キャッシュ）
-- ==============================================
CREATE TABLE IF NOT EXISTS user_period_posts_cache (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    period_id INT NOT NULL,
    combined_post_text LONGTEXT NOT NULL,
    last_aggregated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (period_id) REFERENCES evaluation_periods(id),
    UNIQUE (user_id, period_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================
-- 7. post_ability_points（投稿と能力の紐付け）
-- ==============================================
CREATE TABLE IF NOT EXISTS post_ability_points (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id BIGINT NOT NULL,
    action_index TINYINT NOT NULL,
    ability_id TINYINT NOT NULL,
    quality_level TINYINT NOT NULL,
    point TINYINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (ability_id) REFERENCES non_cog_abilities(id),
    UNIQUE (post_id, action_index, ability_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
