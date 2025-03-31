

class CallBackManager:
    def __init__(self):
        self.handler = {}

    '''注册回调方法装饰器'''
    def register(self, msg_type):
        def decorator(fun):
            self.handler[msg_type] = fun
            return fun
        return decorator

    '''回调方法调度器'''
    def dispatch(self, obj, dict_data):
            handler = self.handler.get(dict_data["type"])
            handler(obj,dict_data["data"])

    @staticmethod
    def default_handler(data):
        print(f"Unhandled message type: {data}")