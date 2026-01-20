from flask import jsonify

class Result:
    """
    统一 API 响应格式
    {
        "code": 200,
        "msg": "success",
        "data": { ... }
    }
    """
    @staticmethod
    def success(data=None, msg="操作成功"):
        return jsonify({
            "code": 200,
            "msg": msg,
            "data": data
        })

    @staticmethod
    def fail(msg="操作失败", code=500):
        return jsonify({
            "code": code,
            "msg": msg,
            "data": None
        })
        
    @staticmethod
    def error(code=400, msg="请求参数错误"):
        return jsonify({
            "code": code,
            "msg": msg,
            "data": None
        })