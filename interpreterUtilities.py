import intbase
import copy

INVALID_TYPE = "INVALID_TYPE"
BAD_POINTER = "BAD_POINTER"

super = intbase.InterpreterBase()

class Var():
    def __init__(self, name, scope_env, evaluated = False):
        self.name = name
        self.value = None
        self.evaluated = evaluated
        self.scope_env = scope_env

class Expression():
    def __init__(self, value, scope_env, evaluated = False):
        self.value = value
        self.evaluated = evaluated
        self.scope_env = copy.deepcopy(scope_env)

class Util():
    @staticmethod
    def coerce_to_bool(value): # responsible for int->bool coercion
        if(type(value) == int):
            return value != 0
        return value
    
    @staticmethod
    def get_type_from_string(value):
        match(value):
            case "bool": return bool
            case "string": return str
            case "int" : return int
            case "void": return type(None)
            case _: return INVALID_TYPE # TODO prob causes a bug with structs. Check back in

    @staticmethod
    def type_to_string(value):
        if(value == int):
            return "int"
        if(value == bool):
            return "bool"
        if(value == str):
            return "string"
        

    @staticmethod
    def get_default_val(return_type):
        match(return_type):
            case "bool": return False
            case "string": return ""
            case "int" : return 0
            case _: return None

