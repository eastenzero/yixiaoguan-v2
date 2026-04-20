# TODO: colleges 表增加 campus 字段

## 背景
R06-4A 中，gateway 传给 Dify 的 `inputs` 已包含 `campus` 键，但当前值固定为空字符串，因为 `colleges` 表尚无该字段。

## 后续工作
1. 在 `services/gateway/app/models/user.py` 的 `College` 模型增加 `campus: Mapped[str]` 字段（nullable 或带默认值）。
2. 编写 Alembic migration：`alembic revision --autogenerate -m "add campus to colleges"`。
3. 编写数据回填脚本（或手动 SQL），为现有学院写入正确校区。
4. 修改 `services/gateway/app/routers/chat.py` 中的 `build_dify_inputs`，将 `campus: ""` 改为 `user.college.campus if user.college else ""`。
5. 更新单测 `test_chat_inputs.py`，补充 campus 非空场景。

## 关联任务
- R06-4A（已完成）
- R06-4B（Dify prompt 注入，由 TX 负责）
