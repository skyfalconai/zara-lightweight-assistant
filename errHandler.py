import traceback
def safe_run(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_data = {
                "success":False,
                "error": str(e),
                "function": func.__name__,
                "trace": traceback.format_exc()
            }
            print(f"Error in {func.__name__}: {str(e)}")
            return error_data
    return wrapper



class ErrorHandler:
    def __init__(self):
        self._wrap_modules()
    
    def _wrap_modules(self):
        for attr_name in dir(self):
            if attr_name.startswith("__"):
                continue
            attr=getattr(self,attr_name)
            if callable(attr):
                setattr(self,attr_name,safe_run(attr))
