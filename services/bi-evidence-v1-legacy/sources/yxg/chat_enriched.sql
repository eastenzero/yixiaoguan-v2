SELECT
  id, conversation_id, user_id,
  query_norm, rag_score, kb_doc_matched, is_answered,
  prompt_tokens, completion_tokens, total_tokens,
  prompt_price, completion_price, total_price, currency,
  latency, created_at,
  staff_id, is_pilot, user_type,
  college_name, class_name, grade_year, campus,
  day_ts, rag_bucket
FROM v_chat_enriched
