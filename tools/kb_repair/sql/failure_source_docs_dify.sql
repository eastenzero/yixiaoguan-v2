\pset format unaligned
\pset fieldsep '\t'
\pset tuples_only on
SELECT id, name, enabled, indexing_status
FROM documents
WHERE dataset_id = '4db0c819-7847-4a95-bf06-5b73a9d41d70'
  AND name ~* '转专业|助学贷款|心理咨询|国际交流项目|交换项目|出国交换|大创项目|大学生创新创业|纪律处分|处分申诉|勤工助学|学科竞赛|学校概况|一卡通挂失|校园卡挂失|实验室安全'
ORDER BY name, id;
