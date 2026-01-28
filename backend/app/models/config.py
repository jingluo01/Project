from app.extensions import db

class SysConfig(db.Model):
    """系统配置表 - 存储动态业务参数"""
    __tablename__ = 'sys_config'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False, comment='配置键名')
    config_value = db.Column(db.String(255), nullable=False, comment='配置内容')
    config_desc = db.Column(db.String(255), comment='配置描述')
    
    @staticmethod
    def get_value(key, default=None):
        config = SysConfig.query.filter_by(config_key=key).first()
        return config.config_value if config else default

    @staticmethod
    def set_value(key, value, desc=None):
        config = SysConfig.query.filter_by(config_key=key).first()
        if config:
            config.config_value = str(value)
            if desc:
                config.config_desc = desc
        else:
            config = SysConfig(config_key=key, config_value=str(value), config_desc=desc)
            db.session.add(config)
        db.session.commit()
