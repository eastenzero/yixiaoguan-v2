import asyncio
import json
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session, get_db
from app.utils.deps import get_current_user
from app.utils.rate_limit import limiter
from app.models.user import User, UserRole
from app.models.conversation import ConversationStatus, SenderType
from app.schemas.chat import ChatSendRequest, ChatSendResponse
from app.services.analytics import (
    record_chat_analytics,
    extract_rag_metrics,
    judge_is_answered,
)
from app.services.conversation_service import (
    get_conversation, add_message, build_message_broadcast_event,
)
from app.services.state_machine import transition
from app.services.dify_client import dify_client
from app.services.ws_manager import manager
from app.services.centrifugo_client import centrifugo
from app.services.announcement_service import (
    get_active_announcements_for_user,
    mark_announcement_read,
)
from app.services.source_evidence import ANSWER_DISCLAIMER, build_source_evidence

logger = logging.getLogger(__name__)
router = APIRouter()
KNOWLEDGE_UPDATED_AT = "2026-08-10"


def _schedule_chat_analytics(
    *,
    conv_id: int,
    user: User,
    raw_query: str,
    response_text: str,
    dify_metadata: dict | None,
):
    async def runner() -> None:
        try:
            async with async_session() as session:
                await record_chat_analytics(
                    session,
                    conv_id=conv_id,
                    user=user,
                    raw_query=raw_query,
                    response_text=response_text,
                    dify_metadata=dify_metadata,
                )
        except Exception as exc:
            logger.warning("Failed to schedule chat analytics for conv=%s: %s", conv_id, exc)

    asyncio.create_task(runner())


@router.post("/send")
@limiter.limit("10/minute")
async def chat_send(
    request: Request,
    body: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    学生发送消息。
    - ai_serving: 保存消息 → 调 Dify → 返回 SSE StreamingResponse
    - pending_teacher / teacher_serving: 保存消息 → WS 广播 → 返回 JSON
    - 其他状态: 403
    """
    # 仅学生可使用此端点
    if current_user.role != UserRole.student:
        raise HTTPException(403, "仅学生可使用 /api/chat/send")

    # 获取并校验会话
    conv = await get_conversation(db, body.conv_id, current_user)
    if not conv:
        raise HTTPException(404, "会话不存在")

    if conv.status == ConversationStatus.resolved:
        await transition(db, conv, "reactivate", actor=current_user)
        _status_data = {
            "type": "status_changed",
            "data": {"conv_id": conv.id, "status": "ai_serving", "previous_status": "resolved"},
        }
        await centrifugo.publish(f"conv:{conv.id}", _status_data)
        await manager.broadcast_to_room(f"conv:{conv.id}", _status_data)

    # 状态检查
    if conv.status not in (
        ConversationStatus.ai_serving,
        ConversationStatus.pending_teacher,
        ConversationStatus.teacher_serving,
    ):
        raise HTTPException(403, f"当前状态 {conv.status.value} 不可发送消息")

    # 1. 保存学生消息到 DB
    student_msg = await add_message(
        db, conv.id, SenderType.student,
        body.content, sender_id=current_user.id,
    )

    # 2. WS 广播学生消息
    _student_event = build_message_broadcast_event(student_msg, conv_id=conv.id)
    await centrifugo.publish(f"conv:{conv.id}", _student_event)
    await manager.broadcast_to_room(f"conv:{conv.id}", _student_event)

    # 3. 根据状态路由
    if conv.status == ConversationStatus.ai_serving:
        # ---- AI 路径：返回 SSE 流 ----
        return StreamingResponse(
            _stream_ai_response(db, conv, current_user, body.content),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # ---- 教师路径：返回 JSON ----
        return ChatSendResponse(
            message_id=student_msg.id,
            conv_id=conv.id,
            sender_type="student",
            content=body.content,
            created_at=student_msg.created_at.isoformat(),
        )


def build_dify_inputs(user: User) -> dict[str, str]:
    """构造传给 Dify 的 inputs 字典（纯函数，便于单测）。"""
    return {
        "college_name": user.college.name if user.college else "",
        "campus": user.college.campus or "" if user.college else "",
        "class_name": user.class_.name if user.class_ else "",
    }


def _entry_cohort(text: str) -> int | None:
    match = re.search(r"(?<!\d)(20)?(\d{2})\s*级", text)
    if not match:
        return None
    return 2000 + int(match.group(2))


def _is_library_hours_query(query: str) -> bool:
    return "图书馆" in query and any(term in query for term in (
        "几点", "开放", "开门", "关门", "闭馆", "时间", "开吗", "周末", "星期",
        "周几", "早上", "中午", "下午", "晚上", "今天", "明天", "自习", "能进",
    ))


def _is_scholarship_query(query: str) -> bool:
    return any(term in query for term in (
        "奖学金", "奖助金", "国奖", "励志奖", "省政府奖", "校级综合奖",
        "弘毅", "自强奖", "自强之星", "新生奖", "济南奖", "评奖评优", "评奖资格",
    ))


def _is_scholarship_overview_query(query: str) -> bool:
    normalized = re.sub(r"[\s，。？！?!、：:]+", "", query)
    return normalized in ("奖学金", "奖助学金", "学校奖学金", "校级奖学金") or any(
        term in normalized for term in (
            "奖学金有哪些", "有哪些奖学金", "奖学金分类", "奖学金种类",
            "奖学金政策", "奖学金介绍", "奖学金汇总", "全部奖学金",
        )
    )


def add_curated_library_sources(sources: list[dict], query: str) -> list[dict]:
    if not _is_library_hours_query(query):
        return sources
    curated = [
        {
            "title": "两校区图书馆日常开放时间（07:00—22:00）",
            "content": "济南校区和泰安校区图书馆周一至周日07:00—22:00开放，下午正常开放。",
            "source_label": "校内执行口径",
            "source_type": "knowledge_base",
            "verified": False,
            "last_verified": "2026-08-10",
            "effective_status": "current",
        },
        {
            "title": "黄河图书馆开馆与场馆介绍",
            "source_url": "https://www.sdfmu.edu.cn/info/1076/12216.htm",
            "content": "学校官网对黄河图书馆启用、建筑规模与服务空间的介绍。",
            "source_label": "学校官网",
            "source_type": "official_web",
            "verified": True,
            "published_at": "2022-11-11",
            "effective_status": "stable",
        },
        {
            "title": "山东第一医科大学全景校园",
            "source_url": "https://www.sdfmu.edu.cn/index/xysh/qjxy.htm",
            "content": "学校官网发布的济南、泰安校区校园实景资料。",
            "source_label": "学校官网",
            "source_type": "official_web",
            "verified": True,
            "effective_status": "stable",
        },
    ]
    known = {item.get("title") for item in sources}
    return sources + [item for item in curated if item["title"] not in known]


def add_curated_scholarship_sources(sources: list[dict], query: str) -> list[dict]:
    if not _is_scholarship_query(query):
        return sources
    curated = [
        {
            "title": "2025年本专科生国家奖助政策简介",
            "source_url": "https://www.gov.cn/zhengce/202507/content_7032288.htm",
            "source_label": "中国政府网",
            "source_type": "official_web",
            "verified": True,
            "published_at": "2025-07",
            "effective_status": "current",
        },
        {
            "title": "调整高等教育阶段国家奖助学金政策的通知",
            "source_url": "https://www.mof.gov.cn/gkml/caizhengwengao/wg2024/wg202410/202501/P020250109539041693223.pdf",
            "source_label": "财政部官网",
            "source_type": "official_web",
            "verified": True,
            "published_at": "2024-10",
            "effective_status": "current",
        },
        {
            "title": "山东省本专科生奖励资助实施细则",
            "source_url": "https://www.yantai.gov.cn/cms_files/jcms1/web1/site/attach/0/b367d29f251242bb9a74c18eaf5ae817.pdf",
            "source_label": "山东省政策文件",
            "source_type": "official_web",
            "verified": True,
            "published_at": "2022",
            "effective_status": "current_reference",
        },
        {
            "title": "山一大2024—2025学年校级综合奖学金评审通知",
            "source_url": "https://sa.sdfmu.edu.cn/info/1341/21131.htm",
            "source_label": "学校官网",
            "source_type": "official_web",
            "verified": True,
            "academic_year": "2024-2025",
            "effective_status": "historical",
        },
        {
            "title": "山一大2024—2025学年“弘毅”奖学金评审通知",
            "source_url": "https://sa.sdfmu.edu.cn/info/1341/21411.htm",
            "source_label": "学校官网",
            "source_type": "official_web",
            "verified": True,
            "academic_year": "2024-2025",
            "effective_status": "historical",
        },
    ]
    if "自强" in query:
        curated.append({
            "title": "2024届自强奖学金名单公示",
            "source_url": "https://sa.sdfmu.edu.cn/info/1341/18451.htm",
            "source_label": "学校官网",
            "source_type": "official_web",
            "verified": True,
            "academic_year": "2024届",
            "effective_status": "historical",
        })
    if "新生奖" in query:
        curated.append({
            "title": "2023级新生奖学金获奖学生名单公示",
            "source_url": "https://sa.sdfmu.edu.cn/info/1341/16851.htm",
            "source_label": "学校官网",
            "source_type": "official_web",
            "verified": True,
            "academic_year": "2023级",
            "effective_status": "historical",
        })
    if "济南奖" in query:
        curated.append({
            "title": "山一大第六届济南奖学金评选通知",
            "source_url": "https://sa.sdfmu.edu.cn/info/1341/21001.htm",
            "source_label": "学校官网",
            "source_type": "official_web",
            "verified": True,
            "academic_year": "2024-2025",
            "effective_status": "historical",
        })
    known = {item.get("title") for item in sources}
    return sources + [item for item in curated if item["title"] not in known]


def build_dify_query(query: str, class_name: str = "") -> str:
    """Inject only the response structure and confirmed local routing needed by the query."""
    contexts = [
        "【统一回答方式】\n"
        "按照成熟校园办事助手的方式组织正文，不介绍系统能力，不先讲免责声明：\n"
        "1. 开头用2—4句话直接回答用户问的能不能、是什么、几点或怎么办。\n"
        "2. 按问题本身自然分段：政策按层级，流程列3—5步，多项比较用短表格或分组。\n"
        "3. 已检索到的内容要具体说清适用对象、条件、时间、材料、入口和负责单位；"
        "不要只回答‘咨询辅导员’或‘以通知为准’。\n"
        "4. 只有会变化的名额、截止日期或未公开的学院口径放入‘仍需核实’，"
        "不得把已知结论藏在保守声明后面。\n"
        "5. 不输出‘知识库尚未接入’、‘后续接入后’、‘系统无法确认’等开发状态文案。\n"
        "6. 简单事实控制在200—400字，单项政策450—800字，复杂比较800—1400字；每段2—4句。\n"
        "7. 参考资料由界面单独展示，正文不重复堆放链接；结尾给出2—3个可直接继续追问的问题。"
    ]

    if _is_library_hours_query(query):
        contexts.append(
            "【已确认的图书馆日常开放口径】\n"
            "济南校区和泰安校区图书馆，周一至周日均为07:00开放、22:00闭馆，"
            "中午和下午正常开放，周末也正常开放。先直接回答这个时间，不得说下午不开放或周末闭馆。"
            "法定节假日、寒暑假、考试周或临时维护可能调整，特殊日期再提示查看图书馆当日通知。"
        )

    if _is_scholarship_query(query):
        if _is_scholarship_overview_query(query):
            contexts.append(
                "【本题已判定为奖学金总览】\n"
                "必须直接输出一篇完整综述，不追问用户想查哪一项，不只回答其中一层。"
                "综述顺序固定为：先用1段总结学校奖学金体系，再分别展开国家级、山东省政府级、"
                "山一大校级、学院及社会专项，最后用1段说明同学年互斥关系与申请时的核对项。"
            )
        contexts.append(
            "【奖学金分层事实与输出顺序】\n"
            "用户泛问时必须依次使用‘一、国家级’、‘二、山东省级’、‘三、山一大校级’、"
            "‘四、学院/社会专项’四个标题，不得合并，也不得先要求补充年级或学院。"
            "每个层级先用1个独立段落说清‘这一层主要奖励哪类学生、包含哪些奖项’，"
            "再换行逐项展开；层级之间必须留出明显分段。\n"
            "一、国家级：\n"
            "先概括：国家级本科奖学金主要分为‘特别优秀奖励’和‘家庭经济困难学生励志奖励’两方面，"
            "具体包括本专科生国家奖学金、本专科生国家励志奖学金。\n"
            "1. 本专科生国家奖学金：全日制本专科二年级及以上，现行每生每年10,000元，"
            "不要求困难认定。山东2022实施细则参考线为学习成绩与综合考评均前10%；"
            "某方面特别突出时两项可放宽至前30%并提交证明。\n"
            "2. 本专科生国家励志奖学金：二年级及以上，现行每生每年6,000元，"
            "必须已认定为家庭经济困难学生；无不及格科目，学习或综测一项前30%、另一项前50%，"
            "特殊困难学生两项可放宽至前50%。\n"
            "二、山东省级：\n"
            "先概括：省级主要包含特别优秀学生奖励、困难学生励志奖励和特定地区少数民族学生专项励志奖励，"
            "具体包括山东省政府奖学金、山东省政府励志奖学金和新疆西藏青海海北籍少数民族专项。\n"
            "1. 山东省政府奖学金：二年级及以上，每生每年6,000元，不要求困难认定；"
            "学习成绩和综合考评均前15%，突出表现可放宽至前30%并提交证明。\n"
            "2. 山东省政府励志奖学金：每生每年5,000元，须困难认定，无不及格科目，"
            "排名规则与国家励志奖学金相同。\n"
            "3. 新疆西藏和青海海北籍少数民族大学生省政府励志奖学金：每生每年5,000元，"
            "限特定入学前户籍、少数民族且已困难认定的学生；当学年排名要求单独核对。\n"
            "国家奖学金、省政府奖学金和各类励志奖学金同学年不可重复获得；"
            "符合困难条件者可同时获得国家助学金。\n"
            "三、山一大校级（以已发布的2024—2025学年通知为参考，不得自动延续为新学年标准）：\n"
            "先概括：校级奖学金主要覆盖学业与综测表现、突出成果、自强成长及新生等方向。"
            "已有较完整官方条件可展开的是校级综合奖学金和‘弘毅’奖学金；"
            "自强奖学金、新生奖学金应列在这一层，但金额与名额须根据当学年通知回答。\n"
            "1. 校级综合奖学金：一等1,500元（比例4%）、二等1,000元（4%）、三等800元（10%）；"
            "学习成绩自然班前30%、综测前40%，无不及格（含V类）、无补考、无过程考核不达标、无违纪。"
            "流程为个人申请→班级评议→学院审核→学院公示不少于2个工作日→学校复核。\n"
            "2. ‘弘毅’奖学金：4,000元，全校每学年不超过50名；学习和综测均前50%，"
            "无不及格、补考或过程考核失败，且在道德、科研、竞赛、发明、实践、体艺等方面有特别突出表现。"
            "材料包括审批表、盖章成绩单、联名推荐信和成果证明；与同学年国家、省政府、励志及济南奖学金互斥。\n"
            "3. 自强奖学金：2024届官方结果显示，自强之星4,000元、提名奖2,000元、入围奖1,000元；"
            "这是2024届结果口径，不得直接说成当年固定标准。\n"
            "4. 新生奖学金：学校官网2023级公示可证明项目存在，但当年金额、名额和对象须根据最新招生与学工通知回答。\n"
            "5. 济南奖学金须单独标注为济南市专项、由学校组织评选，不得归为国家或省政府奖学金。"
            "2024—2025学年第六届通知面向济南校区指定毕业年级，且国家、省级奖学金获得者也可参评；新周期须重新核对通知。\n"
            "四、学院/社会专项：仅在检索命中当学年官方材料时列出，必须写明适用学院，"
            "不得把其他学院的项目说成全校通用。自强、新生等奖学金如无当年通知，须标注参考学年且不臆造金额。\n"
            "每个奖项独立成段，固定展示‘对象｜金额｜核心条件｜困难认定｜互斥关系｜流程/材料’；"
            "研究生和留学生政策另行回答，不套用本科标准。"
        )

    if not any(term in query for term in ("补考", "重修", "挂科", "不及格")):
        return query if not contexts else f"{query}\n\n" + "\n\n".join(contexts)

    cohort = _entry_cohort(query) or _entry_cohort(class_name)
    if cohort is None:
        route = (
            "用户入学年级尚不明确。先追问入学年级；如需在本轮给出帮助，"
            "可并列说明2023级及以前与2024级及以后的两种规则，禁止统一回答。"
        )
    elif cohort <= 2023:
        route = (
            f"已识别为{cohort}级：正常课程考核不及格后原则上仍有一次补考机会；"
            "补考仍不合格再按规定重修。"
        )
    else:
        route = (
            f"已识别为{cohort}级：常规课程考核不及格后不再安排补考，直接按规定重修。"
        )

    contexts.append(
        "【系统补充的校内规则上下文】\n"
        "普通本科生按入学年级分流：2023级及以前原则上保留一次补考机会；"
        "2024级及以后常规挂科后不安排补考，直接重修。\n"
        f"{route}\n"
        "旷考、作弊、取消考试资格、缓考、实践课程、研究生、继续教育和其他特殊培养类型另行核验。"
        "公开网页暂未找到明确写出2024级切换点的正式文件，回答须标注这是当前校内执行口径，"
        "并提示以教务部、学院最新通知及负责部门答复为准。"
    )
    return f"{query}\n\n" + "\n\n".join(contexts)


async def _stream_ai_response(db, conv, user, query: str):
    """
    内部生成器：调 Dify → 逐 token 发 SSE → 最后保存 AI 消息。
    """
    full_answer = ""
    sources = []
    new_dify_conv_id = conv.dify_conversation_id
    message_end_metadata: dict | None = None

    try:
        # R05-4: deliver active unread announcements first
        try:
            announcements = await get_active_announcements_for_user(db, user)
            for ann in announcements:
                ann_event = {
                    "id": ann.id,
                    "title": ann.title,
                    "content": ann.content,
                    "created_by": ann.created_by,
                    "created_at": ann.created_at.isoformat(),
                    "expire_at": ann.expire_at.isoformat(),
                }
                yield f"event: announcement\ndata: {json.dumps(ann_event, ensure_ascii=False)}\n\n"
                await mark_announcement_read(db, user_id=user.id, announcement_id=ann.id)
        except Exception as exc:
            logger.warning("announcement delivery failed for user=%s: %s", user.id, exc)
            # do NOT block chat — announcement delivery is best-effort

        async for event in dify_client.chat_stream(
            query=build_dify_query(
                query,
                user.class_.name if user.class_ else "",
            ),
            user_id=str(user.id),
            conversation_id=conv.dify_conversation_id,
            inputs=build_dify_inputs(user),
        ):
            event_type = event.get("event", "")

            if event_type == "message":
                token = event.get("answer", "")
                full_answer += token
                # 捕获 Dify 新生成的 conversation_id
                if not new_dify_conv_id:
                    new_dify_conv_id = event.get("conversation_id")
                yield f"event: message\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

            elif event_type == "message_end":
                # 提取来源引用
                metadata = event.get("metadata", {})
                message_end_metadata = metadata if isinstance(metadata, dict) else None
                retriever_resources = metadata.get("retriever_resources", [])
                try:
                    sources = await build_source_evidence(
                        db,
                        retriever_resources,
                        user_college=user.college.name if user.college else None,
                        query=query,
                    )
                except Exception as exc:
                    logger.warning("source evidence enrichment failed: %s", exc)
                    sources = [
                        {
                            "title": r.get("document_name", ""),
                            "score": r.get("score", 0),
                            "content": r.get("content", "")[:600],
                            "document_id": r.get("document_id"),
                            "dataset_id": r.get("dataset_id"),
                            "source_label": "校园知识库",
                            "source_type": "knowledge_base",
                            "verified": False,
                        }
                        for r in retriever_resources
                    ]
                sources = add_curated_scholarship_sources(
                    add_curated_library_sources(sources, query), query
                )
                # 不在这里 yield message_end，等保存完再发

            elif event_type == "error":
                err_msg = event.get("message", "AI 服务暂时不可用")
                yield f"event: error\ndata: {json.dumps({'message': err_msg}, ensure_ascii=False)}\n\n"
                return

    except Exception as e:
        logger.error(f"Dify stream error: {e}")
        yield f"event: error\ndata: {json.dumps({'message': 'AI 服务异常，请稍后再试'}, ensure_ascii=False)}\n\n"
        return

    # 保存 AI 消息到 DB
    ai_msg = await add_message(
        db, conv.id, SenderType.ai, full_answer,
        metadata={
            "sources": sources,
            "dify_conversation_id": new_dify_conv_id,
            "answer_notice": ANSWER_DISCLAIMER,
            "knowledge_updated_at": KNOWLEDGE_UPDATED_AT,
        },
    )

    # 更新 Dify conversation_id（首次对话时）
    if new_dify_conv_id and new_dify_conv_id != conv.dify_conversation_id:
        from sqlalchemy import update as sa_update
        from app.models.conversation import Conversation
        await db.execute(
            sa_update(Conversation)
            .where(Conversation.id == conv.id)
            .values(dify_conversation_id=new_dify_conv_id)
        )
        await db.commit()

    # WS 广播 AI 消息
    _ai_event = build_message_broadcast_event(
        ai_msg,
        conv_id=conv.id,
        metadata={
            "sources": sources,
            "answer_notice": ANSWER_DISCLAIMER,
            "knowledge_updated_at": KNOWLEDGE_UPDATED_AT,
        },
    )
    await centrifugo.publish(f"conv:{conv.id}", _ai_event)
    await manager.broadcast_to_room(f"conv:{conv.id}", _ai_event)

    # 发送 message_end
    yield f"event: message_end\ndata: {json.dumps({'full_content': full_answer, 'sources': sources, 'message_id': ai_msg.id, 'answer_notice': ANSWER_DISCLAIMER, 'knowledge_updated_at': KNOWLEDGE_UPDATED_AT}, ensure_ascii=False)}\n\n"

    is_answered = True
    try:
        rag_score, _ = extract_rag_metrics(message_end_metadata or {})
        is_answered = judge_is_answered(rag_score, full_answer)
    except Exception as e:
        logger.warning(f"Answer quality evaluation failed for conv={conv.id}: {e}")

    # R10: 异步生成关联问题推荐
    try:
        suggestions = await dify_client.generate_suggestions(query, full_answer)
        if suggestions:
            yield f"event: suggestions\ndata: {json.dumps({'questions': suggestions}, ensure_ascii=False)}\n\n"
    except Exception as e:
        logger.warning(f"Suggestions generation failed for conv={conv.id}: {e}")

    if not is_answered:
        try:
            yield (
                "event: unanswered_invite\n"
                f"data: {json.dumps({'message_id': ai_msg.id, 'conv_id': conv.id}, ensure_ascii=False)}\n\n"
            )
        except Exception as e:
            logger.warning(f"unanswered_invite emit failed for conv={conv.id}: {e}")

    yield "event: done\ndata: {}\n\n"
    _schedule_chat_analytics(
        conv_id=conv.id,
        user=user,
        raw_query=query,
        response_text=full_answer,
        dify_metadata=message_end_metadata,
    )
