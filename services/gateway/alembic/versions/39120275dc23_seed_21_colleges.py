"""seed 21 real colleges with campus

Revision ID: 39120275dc23
Revises: 9e879653d552
Create Date: 2026-04-27

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "39120275dc23"
down_revision: Union[str, Sequence[str], None] = "9e879653d552"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLLEGES = [
    (1, "临床与基础医学院", "济南校区"),
    (2, "护理学院", "济南校区"),
    (3, "药学院", "济南校区"),
    (4, "公共卫生与健康管理学院", "济南校区"),
    (5, "眼科学院", "济南校区"),
    (6, "预防医学科学学院", "济南校区"),
    (7, "生物医学科学学院", "济南校区"),
    (8, "实验动物学院", "济南校区"),
    (9, "医疗保障学院", "济南校区"),
    (10, "放射学院", "泰安校区"),
    (11, "口腔医学院", "济南校区"),
    (12, "运动医学与康复学院", "泰安校区"),
    (13, "生命科学学院", "泰安校区"),
    (14, "医学信息与人工智能学院", "济南校区"),
    (15, "化学与制药工程学院", "泰安校区"),
    (16, "马克思主义学院", "泰安校区"),
    (17, "医药管理学院", "泰安校区"),
    (18, "外国语学院", "泰安校区"),
    (19, "继续教育学院", "泰安校区"),
    (20, "国际教育学院", "泰安校区"),
    (21, "通识教育部", "济南校区"),
]


def upgrade() -> None:
    values_sql = ",\n    ".join(
        f"({cid}, '{name.replace(chr(39), chr(39)*2)}', '{campus}')"
        for cid, name, campus in COLLEGES
    )
    op.execute(
        f"""
        INSERT INTO colleges (id, name, campus) VALUES
            {values_sql}
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            campus = EXCLUDED.campus;
        """
    )
    op.execute(
        "SELECT setval('colleges_id_seq', GREATEST((SELECT MAX(id) FROM colleges), 21));"
    )


def downgrade() -> None:
    # Intentionally a no-op. Removing colleges would break users.college_id FK refs.
    # If you need to roll back this seed, do it manually after backing up users/classes.
    pass
