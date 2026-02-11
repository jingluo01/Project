from app.extensions import db

class SchoolMember(db.Model):
    """
    学校官方师生信息表 (位于外部数据库 school_official)
    仅用于注册时的交叉验证
    """
    __bind_key__ = 'school_db'  # 关键：指定链接到 config.py 中的 school_db
    __tablename__ = 'school_members'
    
    # 假设学校数据库的字段结构
    user_no = db.Column(db.String(20), primary_key=True, comment='学号/工号')
    real_name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    member_type = db.Column(db.Integer, nullable=False, comment='类型: 1-学生, 2-教职工')
    department = db.Column(db.String(100), comment='所属院系/部门')
    
    def to_dict(self):
        return {
            'user_no': self.user_no,
            'real_name': self.real_name,
            'member_type': self.member_type,
            'department': self.department
        }
