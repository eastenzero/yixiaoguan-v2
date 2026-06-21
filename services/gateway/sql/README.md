# services/gateway/sql/

存放**不走 alembic** 的辅助 SQL（语义层 VIEW、BI 只读账号、临时数据修复脚本等）。

> 为什么不走 alembic：alembic 适合"业务表 schema 演进"。VIEW 是 BI 专用、可独立 drop/recreate，进 alembic 会把版本树搞得很乱；只读账号更是部署一次性事件。

## 文件

| 文件 | 作用 | 幂等？ |
|---|---|---|
| `bi_views.sql` | 7 个 BI 语义层 VIEW（v_users_dim / v_events_enriched / ...） | ✅ 全部 CREATE OR REPLACE |
| `bi_role.sql` | 创建 `ro_bi` 只读账号 | ✅ 用 DO 块判断角色已存在 |

## Apply 流程（TX-New 上）

### 首次 apply

```bash
ssh tx-new
cd /home/easten/dev/yixiaoguan-v2/services/gateway/sql

# 1. 生成 ro_bi 密码并替换 placeholder（不要把真实密码 commit 进 git）
RO_BI_PWD=$(openssl rand -hex 16)
echo "ro_bi password (save it): $RO_BI_PWD"
sed "s|<REPLACE_ME_32_HEX>|$RO_BI_PWD|g" bi_role.sql > /tmp/bi_role.applied.sql

# 2. 创建账号
docker exec -i yx_postgres psql -U yx_admin -d yixiaoguan_v2 < /tmp/bi_role.applied.sql

# 3. 落 VIEW
docker exec -i yx_postgres psql -U yx_admin -d yixiaoguan_v2 < bi_views.sql

# 4. 验证 7 个 VIEW 可读
for v in v_users_dim v_events_enriched v_chat_enriched v_kpi_daily v_funnel_user v_service_heat v_unanswered_cross; do
  echo "── $v ──"
  docker exec yx_postgres psql -U ro_bi -d yixiaoguan_v2 -c "SELECT count(*) FROM $v;" 2>&1 | tail -3
done

# 5. 清理 /tmp/bi_role.applied.sql（密码明文）
rm /tmp/bi_role.applied.sql
```

### 后续修改 VIEW

只需重跑 `bi_views.sql`（CREATE OR REPLACE 幂等）：

```bash
ssh tx-new
docker exec -i yx_postgres psql -U yx_admin -d yixiaoguan_v2 \
  < /home/easten/dev/yixiaoguan-v2/services/gateway/sql/bi_views.sql
```

### 改密 / 删账号

```bash
# 改密
docker exec yx_postgres psql -U yx_admin -d yixiaoguan_v2 \
  -c "ALTER ROLE ro_bi WITH PASSWORD '<new>';"

# 完全删除（先撤权再 drop）
docker exec yx_postgres psql -U yx_admin -d yixiaoguan_v2 << 'SQL'
REVOKE ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public FROM ro_bi;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM ro_bi;
REVOKE USAGE ON SCHEMA public FROM ro_bi;
REVOKE CONNECT ON DATABASE yixiaoguan_v2 FROM ro_bi;
DROP ROLE ro_bi;
SQL
```

## 凭据存放

- `ro_bi` 密码 → 存到 `services/bi-evidence/.env`（gitignore）
- `services/bi-evidence/.env.schema` 是 git 跟踪的模板（无真实密码）

## 设计文档

详见 `.tasks/bi-evidence-design-20260509.md` §2。
