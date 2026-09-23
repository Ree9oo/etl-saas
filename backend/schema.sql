-- 轻量多源数据同步 ETL SaaS 系统 建表 SQL
-- 由 SQLAlchemy ORM 自动生成（dialect=mysql），可直接在对应数据库中执行
SET NAMES utf8mb4;

CREATE TABLE licenses (
	id INTEGER NOT NULL COMMENT '授权ID' AUTO_INCREMENT, 
	license_code VARCHAR(128) NOT NULL COMMENT '授权码', 
	plan VARCHAR(16) NOT NULL COMMENT '套餐(paid)', 
	status VARCHAR(16) NOT NULL COMMENT '状态(active/invalid)', 
	holder VARCHAR(128) COMMENT '持有者', 
	activated_at DATETIME COMMENT '激活时间', 
	expires_at DATETIME COMMENT '过期时间', 
	remark TEXT COMMENT '备注', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	updated_at DATETIME NOT NULL COMMENT '更新时间', 
	PRIMARY KEY (id)
)

;


CREATE TABLE system_configs (
	id INTEGER NOT NULL COMMENT '配置ID' AUTO_INCREMENT, 
	`key` VARCHAR(64) NOT NULL COMMENT '配置键', 
	value TEXT COMMENT '配置值', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	updated_at DATETIME NOT NULL COMMENT '更新时间', 
	PRIMARY KEY (id), 
	CONSTRAINT uq_syscfg_key UNIQUE (`key`)
)

;


CREATE TABLE users (
	id INTEGER NOT NULL COMMENT '用户ID' AUTO_INCREMENT, 
	username VARCHAR(64) NOT NULL COMMENT '用户名', 
	password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值', 
	`role` VARCHAR(16) NOT NULL COMMENT '角色(admin/user)', 
	plan VARCHAR(16) NOT NULL COMMENT '套餐(free/paid)', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	updated_at DATETIME NOT NULL COMMENT '更新时间', 
	PRIMARY KEY (id)
)

;


CREATE TABLE datasources (
	id INTEGER NOT NULL COMMENT '数据源ID' AUTO_INCREMENT, 
	user_id INTEGER NOT NULL COMMENT '所属用户ID', 
	name VARCHAR(128) NOT NULL COMMENT '数据源名称', 
	db_type VARCHAR(32) NOT NULL COMMENT '数据库类型(mysql/sqlserver/postgresql/oracle/dm/sqlite)', 
	host VARCHAR(255) NOT NULL COMMENT '主机地址', 
	port INTEGER NOT NULL COMMENT '端口', 
	username VARCHAR(128) NOT NULL COMMENT '连接用户名', 
	password TEXT NOT NULL COMMENT '连接密码(已加密)', 
	`database` VARCHAR(128) NOT NULL COMMENT '数据库名/SID', 
	charset VARCHAR(32) COMMENT '字符集', 
	extra TEXT COMMENT '扩展参数(JSON)', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	updated_at DATETIME NOT NULL COMMENT '更新时间', 
	PRIMARY KEY (id), 
	CONSTRAINT uq_ds_user_name UNIQUE (user_id, name), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE sync_tasks (
	id INTEGER NOT NULL COMMENT '任务ID' AUTO_INCREMENT, 
	user_id INTEGER NOT NULL COMMENT '所属用户ID', 
	name VARCHAR(128) NOT NULL COMMENT '任务名称', 
	source_id INTEGER NOT NULL COMMENT '源数据源ID', 
	target_id INTEGER NOT NULL COMMENT '目标数据源ID', 
	source_table VARCHAR(128) NOT NULL COMMENT '源表名', 
	target_table VARCHAR(128) NOT NULL COMMENT '目标表名', 
	mode VARCHAR(16) NOT NULL COMMENT '同步模式(full/incremental)', 
	write_mode VARCHAR(16) NOT NULL COMMENT '写入模式(append/truncate)', 
	inc_field VARCHAR(64) COMMENT '增量字段名(update_time等)', 
	where_condition TEXT COMMENT '自定义WHERE条件', 
	columns TEXT COMMENT '指定字段(逗号分隔,空=全部)', 
	batch_size INTEGER NOT NULL DEFAULT 5000 COMMENT '每批读取/写入行数',
	cron VARCHAR(64) NOT NULL COMMENT 'Cron表达式(空=不定时)', 
	enabled BOOL NOT NULL COMMENT '是否启用调度', 
	status VARCHAR(16) NOT NULL COMMENT '任务状态(idle/running/success/failed)', 
	last_run_at DATETIME COMMENT '上次运行时间', 
	last_sync_value VARCHAR(64) COMMENT '上次增量水位值', 
	retry_count INTEGER NOT NULL COMMENT '失败重试次数', 
	timeout INTEGER NOT NULL COMMENT '超时秒数', 
	last_rows INTEGER NOT NULL COMMENT '上次同步行数', 
	last_duration FLOAT NOT NULL COMMENT '上次同步耗时(秒)', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	updated_at DATETIME NOT NULL COMMENT '更新时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(source_id) REFERENCES datasources (id), 
	FOREIGN KEY(target_id) REFERENCES datasources (id)
)

;


CREATE TABLE task_logs (
	id INTEGER NOT NULL COMMENT '日志ID' AUTO_INCREMENT, 
	user_id INTEGER NOT NULL COMMENT '所属用户ID', 
	task_id INTEGER NOT NULL COMMENT '任务ID', 
	task_name VARCHAR(128) COMMENT '任务名称', 
	status VARCHAR(16) NOT NULL COMMENT '执行状态(running/success/failed)', 
	`rows` INTEGER NOT NULL COMMENT '同步行数', 
	duration FLOAT NOT NULL COMMENT '耗时(秒)', 
	error TEXT COMMENT '错误信息', 
	started_at DATETIME NOT NULL COMMENT '开始时间', 
	finished_at DATETIME COMMENT '完成时间', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	updated_at DATETIME NOT NULL COMMENT '更新时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(task_id) REFERENCES sync_tasks (id)
)

;


CREATE TABLE user_action_logs (
	id INTEGER NOT NULL COMMENT '日志ID' AUTO_INCREMENT,
	user_id INTEGER NOT NULL COMMENT '操作人ID',
	username VARCHAR(64) NOT NULL COMMENT '操作人用户名',
	module VARCHAR(64) NOT NULL COMMENT '功能模块',
	action VARCHAR(64) NOT NULL COMMENT '操作动作',
	detail TEXT COMMENT '操作详情',
	ip_address VARCHAR(64) NOT NULL DEFAULT '' COMMENT '访问IP',
	created_at DATETIME NOT NULL COMMENT '操作时间',
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
