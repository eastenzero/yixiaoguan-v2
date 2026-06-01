SELECT
  id, staff_id, name, role,
  college_id, college_name, campus,
  class_id, class_name, grade_year,
  is_pilot, user_type, is_active, joined_at
FROM v_users_dim
