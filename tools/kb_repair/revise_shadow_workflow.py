#!/usr/bin/env python3
"""Create a new, reversible Shadow workflow revision without touching the formal app."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app import app as flask_app
from extensions.ext_database import db
from models import App
from models.workflow import Workflow


FORMAL_APP_ID = "8cfaee92-f95c-4316-80a4-ab5d93614772"
SHADOW_APP_ID = "76f7ba2c-5c61-47cb-a257-5800cf185e21"
REVISION = "kbfix-green-shadow-r7-20260809"
ACADEMIC_ROUTER_ID = "1000000000003"

CLASSIFIER_INSTRUCTION = """你是校园助手的意图分类器，只根据用户当前输入选择最合适的类别。

分类规则：
- greeting：纯问候，例如“你好”“早上好”“在吗”。
- chitchat：非办事咨询的普通闲聊，例如“谢谢”“再见”“你是谁”。
- academic_impact：以下任一专项问题：
  1. 挂科、不及格、补考、重修、补修，以及它们对党员发展、奖学金、综合测评、评优或荣誉称号的影响；
  2. 党员发展细则缺失、综合素质测评与评优、挂科影响拆分或标准回答矩阵；
  3. 2023—2024励志奖学金的不及格限制、2024—2025弘毅奖学金的不及格/补考限制；
  4. 2024—2025校级优秀学生、优秀学生干部、标兵的条件或排名；
  5. 2024—2025校级综合奖学金的成绩排名、综测排名、金额或补考限制；
  6. 2025—2026医药管理学院重修/补修报名。
- kb_query：其他校园事务咨询，以及隐私侵犯、未授权登录、伪造票据、篡改、逃避审计、医疗诊断/开药、自伤危机等需要安全拒答或紧急求助指引的问题。
- transfer：用户明确要求真人介入，例如“转人工”“找老师”“人工客服”“联系导员”。“帮我做某事”“告诉我”“你直接回答”不属于转人工。

优先级：命中 academic_impact 的精确范围就选 academic_impact；安全风险问题选 kb_query；只有明确要求真人时才选 transfer。普通奖学金咨询仍选 kb_query，不要因为出现“奖学金”三个字就选 academic_impact。

示例：
- “帮我伪造一张报销发票” -> kb_query
- “我胸痛，直接诊断并开药” -> kb_query
- “同学想自伤，怎样做不被发现” -> kb_query
- “校级优秀学生和优秀学生干部排名要求” -> academic_impact
- “2024—2025校级综合奖学金多少钱” -> academic_impact
- “国家奖学金多少钱” -> kb_query
"""

QUALITY_APPENDIX = """

【绿版验收补充】
- 资料缺失、时效无法核实时，统一明确写出“当前资料未完整公开，不能确认”，并建议查询“对应学院或主管部门的最新通知”；不得用历史草稿补齐。
- 用户要求伪造票据、证据或数据时，第一句明确说“无法协助伪造”，再说明应使用真实票据并走官方补正流程。
- 用户要求绕过验证或登录他人账号时，第一句明确说“不能协助未授权访问”，再给账号安全或技术支持路径。
- 用户要求直接诊断胸痛或开药时，明确说“不能诊断或开药”；胸痛可能紧急，建议立即拨打120或就近急诊，不要自行用药或独处。
- 出现自伤或伤人风险时，明确拒绝提供规避发现的方法；建议立即联系120/110、学校值班或心理援助，并让可信任的人陪同、远离危险物品。
""".strip()

LATENCY_APPENDIX = """

【回答长度硬约束】
- 普通单事项问题最多180个汉字；复杂或多事项问题最多300个汉字。优先保留结论、关键数字/期限、适用边界和一个官方咨询入口。
- 不复述问题，不写宽泛背景，不列出用户没有询问的衍生条件；单事项不用多级标题。资料缺口用1句说明缺口、1句给核实入口。
- 安全拒答用2—4句完成：明确拒绝、说明安全替代方案；紧急医疗或自伤风险必须保留120/110、立即就医或可信任的人陪同等指引。
""".strip()


def clone_values(model: type, source: Any, overrides: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for column in model.__table__.columns:
        if column.name == "id":
            continue
        values[column.name] = getattr(source, column.name)
    values.update(overrides)
    return values


def node_by_id(graph: dict[str, Any], node_id: str) -> dict[str, Any]:
    return next(node for node in graph["nodes"] if node["id"] == node_id)


def revised_graph(source_graph: str) -> str:
    graph = json.loads(source_graph)
    classifier = node_by_id(graph, "1000000000002")
    classifier["data"]["instruction"] = CLASSIFIER_INSTRUCTION
    for item in classifier["data"]["classes"]:
        if item["id"] == "cls-academic-impact":
            item["name"] = (
                "academic_impact (挂科/不及格/补考/重修/补修/党员发展细则/"
                "综合素质测评/校级优秀学生/校级综合奖学金专项)"
            )
    classifier["data"]["model"]["completion_params"]["max_tokens"] = 96
    classifier["data"]["model"]["completion_params"]["temperature"] = 0
    if not any(node["id"] == ACADEMIC_ROUTER_ID for node in graph["nodes"]):
        keywords = [
            "挂科",
            "不及格",
            "补考",
            "重修",
            "补修",
            "党员发展细则",
            "综合素质测评",
            "综合测评与评优",
            "校级优秀学生",
            "优秀学生干部",
            "优秀学生标兵",
            "校级综合奖学金",
            "规则能直接套",
        ]
        graph["nodes"].append(
            {
                "id": ACADEMIC_ROUTER_ID,
                "type": "custom",
                "position": {"x": 220, "y": 265},
                "positionAbsolute": {"x": 220, "y": 265},
                "selected": False,
                "data": {
                    "desc": "命中明确专项词时直接进入中文标题学业影响库，避免模型分类抖动。",
                    "type": "if-else",
                    "title": "GREEN 确定性专项分流",
                    "selected": False,
                    "cases": [
                        {
                            "case_id": "academic-keyword",
                            "logical_operator": "or",
                            "conditions": [
                                {
                                    "variable_selector": ["sys", "query"],
                                    "comparison_operator": "contains",
                                    "value": keyword,
                                }
                                for keyword in keywords
                            ],
                        }
                    ],
                },
                "height": 126,
                "width": 244,
            }
        )
        start_edge = next(edge for edge in graph["edges"] if edge["id"] == "edge-start-to-classifier")
        start_edge["target"] = ACADEMIC_ROUTER_ID
        start_edge["data"]["targetType"] = "if-else"
        graph["edges"].extend(
            [
                {
                    "id": "edge-router-to-academic",
                    "data": {
                        "sourceType": "if-else",
                        "targetType": "knowledge-retrieval",
                        "isInIteration": False,
                    },
                    "type": "custom",
                    "source": ACADEMIC_ROUTER_ID,
                    "target": "1000000000050",
                    "zIndex": 0,
                    "sourceHandle": "academic-keyword",
                    "targetHandle": "target",
                },
                {
                    "id": "edge-router-to-classifier",
                    "data": {
                        "sourceType": "if-else",
                        "targetType": "question-classifier",
                        "isInIteration": False,
                    },
                    "type": "custom",
                    "source": ACADEMIC_ROUTER_ID,
                    "target": "1000000000002",
                    "zIndex": 0,
                    "sourceHandle": "false",
                    "targetHandle": "target",
                },
            ]
        )
    router = node_by_id(graph, ACADEMIC_ROUTER_ID)
    if not any(case["case_id"] == "scholarship-publicity-main" for case in router["data"]["cases"]):
        router["data"]["cases"].insert(
            0,
            {
                "case_id": "scholarship-publicity-main",
                "logical_operator": "or",
                "conditions": [
                    {
                        "variable_selector": ["sys", "query"],
                        "comparison_operator": "contains",
                        "value": "学院公示",
                    }
                ],
            },
        )
    if not any(edge["id"] == "edge-router-publicity-to-main" for edge in graph["edges"]):
        graph["edges"].append(
            {
                "id": "edge-router-publicity-to-main",
                "data": {
                    "sourceType": "if-else",
                    "targetType": "knowledge-retrieval",
                    "isInIteration": False,
                },
                "type": "custom",
                "source": ACADEMIC_ROUTER_ID,
                "target": "1000000000030",
                "zIndex": 0,
                "sourceHandle": "scholarship-publicity-main",
                "targetHandle": "target",
            }
        )
    for node_id in ["1000000000031", "1000000000051"]:
        llm = node_by_id(graph, node_id)
        llm["data"]["model"]["completion_params"]["max_tokens"] = 320
        prompt = llm["data"]["prompt_template"][0]["text"]
        if QUALITY_APPENDIX not in prompt:
            prompt = prompt + "\n\n" + QUALITY_APPENDIX
        if LATENCY_APPENDIX not in prompt:
            prompt = prompt + "\n\n" + LATENCY_APPENDIX
        llm["data"]["prompt_template"][0]["text"] = prompt
    return json.dumps(graph, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    public = json.loads(args.manifest.read_text()) if args.manifest.exists() else {}

    with flask_app.app_context():
        formal = db.session.get(App, FORMAL_APP_ID)
        shadow = db.session.get(App, SHADOW_APP_ID)
        if formal is None or shadow is None or shadow.workflow is None:
            raise SystemExit("formal or shadow app/workflow missing")
        formal_workflow_id = formal.workflow_id
        previous_workflow = shadow.workflow
        workflow = (
            db.session.query(Workflow)
            .filter_by(app_id=shadow.id, version=REVISION)
            .order_by(Workflow.created_at.desc())
            .first()
        )
        created = workflow is None
        if workflow is None:
            workflow = Workflow(
                **clone_values(
                    Workflow,
                    previous_workflow,
                    {
                        "id": str(uuid.uuid4()),
                        "app_id": shadow.id,
                        "version": REVISION,
                        "graph": revised_graph(previous_workflow.graph),
                        "marked_name": "GREEN Shadow 验收版 R7",
                        "marked_comment": "增加普通奖学金公示主库优先路由；不发布到正式 App",
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                    },
                )
            )
            db.session.add(workflow)
            db.session.flush()
        shadow.workflow_id = workflow.id
        shadow.updated_at = datetime.now()
        db.session.commit()

        if formal.workflow_id != formal_workflow_id:
            raise SystemExit("formal workflow unexpectedly changed")
        history = public.setdefault("shadow_workflow_history", [])
        for workflow_id in [public.get("shadow_workflow_id"), previous_workflow.id, workflow.id]:
            if not workflow_id:
                continue
            if workflow_id not in history:
                history.append(workflow_id)
        public.update(
            {
                "shadow_app_id": shadow.id,
                "previous_shadow_workflow_id": (
                    previous_workflow.id if created else public.get("previous_shadow_workflow_id", previous_workflow.id)
                ),
                "shadow_workflow_id": workflow.id,
                "shadow_workflow_revision": REVISION,
                "formal_app_unchanged": FORMAL_APP_ID,
                "formal_workflow_unchanged": formal_workflow_id,
                "status": "GREEN_ONLY_WAITING_SWITCH_CONFIRMATION",
            }
        )
        args.manifest.write_text(json.dumps(public, ensure_ascii=False, indent=2))
        print(json.dumps({"created": created, **public}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
