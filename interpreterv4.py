from brewparse import parse_program
from intbase import InterpreterBase
from intbase import ErrorType
import copy

RETURN = "RETURN"
DEBUG_MODE = False
RAISE = "RAISE"

from interpreterUtilities import Var
from interpreterUtilities import Expression
from interpreterTests import testFramework

class Interpreter(InterpreterBase):
    func_dict = {}  # Maps (func_name, num_args) to the related function

    def debug_scope_env(self, scope_env):
        scope_count = 0
        for scope in scope_env:
            print("  " * scope_count + "-- Scope " + str(scope_count) + " --")
            for key in scope.keys():
                var_ref = self.get_var_ref(key, scope_env)
                print("  " * (scope_count+1) + key + " = " + str(var_ref.value))

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
    
    def def_var(self, var_name, scope_env):
        if(var_name in scope_env[0].keys()):
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} defined more than once")
                return (RETURN, None)
        scope_env[0][var_name] = Var(var_name, copy.deepcopy(scope_env))  # Add empty var spot in current scope

    def get_var_ref(self, var_name, scope_env):
        for scope in scope_env:
            if(var_name in scope.keys()):
                return scope[var_name]
        super().error(ErrorType.NAME_ERROR, f"Variable {var_name} is undefined")

    def get_var_val(self, var_name, scope_env):
        var_ref = self.get_var_ref(var_name, scope_env)
        if(DEBUG_MODE):
            print("getting value of " + var_name)
        if(not var_ref.evaluated):
            if(DEBUG_MODE):
                print(var_name + " not evaluated, about to evaluate. Current value: " + str(var_ref.value))
            var_ref.value = self.get_expression_value(var_ref.value, var_ref.scope_env)
            var_ref.evaluated = True
        return var_ref.value

    def set_var(self, var_name, value, scope_env):
        var_ref = self.get_var_ref(var_name, scope_env)
        var_ref.value = value
        var_ref.scope_env = copy.deepcopy(scope_env)
        if(DEBUG_MODE):
            print("setting var: " + var_ref.name)
            self.debug_scope_env(var_ref.scope_env)
        
    # returns a formatted error if operands don't match any allowed types
    def type_check(self, op1, op2, allowed_types, operation_name, strict):

        if (type(op1) in allowed_types and type(op2) in allowed_types):
            return True
        elif(strict): # If strict true, any deviation should cause immediate exit
            super().error(ErrorType.TYPE_ERROR, f"Incompatible types for {operation_name}: {type(op1)}, {type(op2)}")
        else:
            return False

    def type_check_unary(self, op1, allowed_types, operation_name, strict):
        if (type(op1) in allowed_types):
            return True
        elif(strict): # If strict true, any deviation should cause immediate exit
            super().error(ErrorType.TYPE_ERROR, f"Incompatible type for {operation_name}: {type(op1)}")
        else:
            return False
        
    def run(self, program_source):
        super().reset()
        self.var_dict = {}
        program = parse_program(program_source)
        main_func = None

        for function in program.dict["functions"]:
            self.func_dict[(function.dict["name"], len(function.dict["args"]))] = function 
        
        main_func = self.func_dict[("main", 0)]
        if(main_func == None):
            super().error(ErrorType.NAME_ERROR, "No main function found")
            return -1
        
        self.run_func(main_func)

        

    def run_func(self, function, args = []):
        scope_env = [{}]

        if(len(args) != len(function.dict["args"])):
           super().error(ErrorType.TYPE_ERROR, f"Invalid number of arguments for function")
            
        arg_names = [item.dict["name"] for item in function.dict["args"]]
        for exp_node, arg_name in zip(args, arg_names): # populate local scope with argument nodes
            self.def_var(arg_name, scope_env)
            self.set_var(arg_name, exp_node, scope_env)

        for statement in function.dict["statements"]:
            statement_output = self.run_statement(statement, scope_env)
            if (statement_output != None): 
                if(type(statement_output) == tuple and statement_output[0] == RETURN):
                    return statement_output[1]
                if(type(statement_output) == tuple and statement_output[0] == RAISE and function.dict["name"] == "main"):
                    # unhandled exception!
                    super().error(ErrorType.FAULT_ERROR, f"Unhandled exception! {statement_output[1]}")
                else:
                    return statement_output
        scope_env.pop(0)  # pop scope when function complete
        return None

    def run_statement(self, statement, scope_env):
        # Variable definition
        if statement.elem_type == "vardef":
            var_name = statement.dict["name"]
            self.def_var(var_name, scope_env)

        # Assignment
        elif statement.elem_type == "=":
            var_name  = statement.dict["name"]
            self.set_var(var_name, Expression(statement.dict["expression"], scope_env), scope_env)

        # Function call
        elif statement.elem_type == "fcall":
            return self.get_expression_value(self.exec_func(statement.dict["name"], statement.dict["args"], scope_env), scope_env)

        # Raise Call
        elif statement.elem_type == "raise":
            except_type = self.get_expression_value(statement.dict["exception_type"], scope_env)
            self.type_check_unary(except_type, [str], "raise statement", True)
            if(DEBUG_MODE):
                print("raised exception: " + except_type)
            return (RAISE, except_type)
        # Try block
        elif statement.elem_type == "try":
            scope_env.insert(0, {})
            output = None
            if(statement.dict["statements"] != None):
                for line in statement.dict["statements"]:
                    statement_output = self.run_statement(line, scope_env)
                    if (statement_output != None): 
                        scope_env.pop()
                        if(type(statement_output) == tuple and statement_output[0] == RETURN):
                            return statement_output
                        if(type(statement_output) == tuple and statement_output[0] == RAISE):
                            for catch in statement.dict["catchers"]:
                                if(catch.dict["exception_type"] == statement_output[1]):
                                    return self.run_statement(catch, scope_env)
                            if (DEBUG_MODE):
                                print("no catchers found")
                            return statement_output
                        else:
                            output = statement_output
                                 
                # No catchers.
                return output

        # Catch block
        elif statement.elem_type == "catch":
            if(DEBUG_MODE):
                print("Caught exception")
            scope_env.insert(0, {})
            if(statement.dict["statements"] != None):
                for line in statement.dict["statements"]:
                    statement_output = self.run_statement(line, scope_env)
                    if(statement_output != None):
                        return statement_output

        # If statement
        elif statement.elem_type == "if":
            new_scope = {}
            scope_env.insert(0, new_scope)  # push scope to top of stack
            statements = []
            condition = self.get_expression_value(statement.dict["condition"], scope_env)
            self.type_check_unary(condition, [bool], "if statement condition", True)
            if(condition):
                statements = statement.dict["statements"]
            else:
                statements = statement.dict["else_statements"]

            if(statements != None):
                for statement in statements:
                    statement_output = self.run_statement(statement, scope_env)
                    if (statement_output != None): 
                        if(type(statement_output) == tuple and statement_output[0] == RETURN):
                            return statement_output[1]
                        else:
                            return statement_output
            
            scope_env.pop(0)  # pop scope when complete

        elif statement.elem_type == "for":
            new_scope = {}
            scope_env.insert(0, new_scope)
            self.run_statement(statement.dict["init"], scope_env)
            condition = self.get_expression_value(statement.dict["condition"], scope_env)
            self.type_check_unary(condition, [bool], "if statement condition", True)
            while(self.get_expression_value(statement.dict["condition"], scope_env)):
                for step in statement.dict["statements"]:
                    statement_output = self.run_statement(step, scope_env)
                    if (statement_output != None): 
                        if(type(statement_output) == tuple and statement_output[0] == RETURN):
                            return statement_output[1]
                        else:
                            return statement_output
                self.run_statement(statement.dict["update"], scope_env)

        elif statement.elem_type == "return":
            return (RETURN, Expression(statement.dict["expression"], scope_env,))

        # Invalid statement type
        else:
            super().error(ErrorType.NAME_ERROR, f"Invalid statement type: {statement.elem_type}")

    # Handles literals, variables, and expressions
    def get_expression_value(self, expression, scope_env):
        if(expression == None): return None

        if(type(expression) == Expression):
            return self.get_expression_value(expression.value, expression.scope_env)

        if(type(expression) == tuple):
            if(expression[0] == RETURN or expression[0] == RAISE):
                return expression

        if(expression.elem_type in ["int", "string", "bool"]):
            return expression.dict["val"]
        
        if(expression.elem_type == "nil"):
            return None

        if(expression.elem_type == "var"):
            var_ref = self.get_var_ref(expression.dict["name"], scope_env)
            if(DEBUG_MODE):
                print("getting var: " + var_ref.name)
                self.debug_scope_env(var_ref.scope_env)
            return self.get_var_val(expression.dict["name"], scope_env)


        # 2-operand operations
        if(expression.elem_type in ["+", "-", "*", "/", "==", "<", "<=", ">", ">=", "!=", "&&", "||"]):
            op1 = self.get_expression_value(expression.dict["op1"], scope_env)

            if(self.type_check_unary(op1, [bool], expression.elem_type, False)):
                if(expression.elem_type in ["&&", "||"]):
                    match(expression.elem_type):
                        case "&&": 
                            if not op1: return False
                            else: 
                                op2 = self.get_expression_value(expression.dict["op2"], scope_env)
                                if(self.type_check_unary(op2, [bool], expression.elem_type, True)):
                                    return op2
                        case "||": 
                            if op1: return True
                            else: 
                                op2 = self.get_expression_value(expression.dict["op2"], scope_env)
                                if(self.type_check_unary(op2, [bool], expression.elem_type, True)):
                                    return op2
                        case _: super().error(ErrorType.TYPE_ERROR, f"Incompatible types for expression.elem_type: {type(op1)}, {type(op2)}") 

                op2 = self.get_expression_value(expression.dict["op2"], scope_env)
                match(expression.elem_type):
                    case "==": return op1 == op2
                    case "!=": return op1 != op2

                    case _: super().error(ErrorType.TYPE_ERROR, f"Incompatible types for expression.elem_type: {type(op1)}, {type(op2)}")

            
            op2 = self.get_expression_value(expression.dict["op2"], scope_env)
            
            # If both operands integers, perform integer operation
            if(self.type_check(op1, op2, [int], expression.elem_type, False)):
                match (expression.elem_type):
                    case "+" : return op1 + op2
                    case "-" : return op1 - op2
                    case "*" : return op1 * op2
                    case "/" : 
                        if(op2 == 0): return (RAISE, "div0")
                        return op1 // op2
                    case ">" : return op1 > op2
                    case ">=": return op1 >= op2
                    case "<" : return op1 < op2
                    case "<=": return op1 <= op2
                    case "==": return op1 == op2
                    case "!=": return op1 != op2
                    case "_" : super().error(ErrorType.TYPE_ERROR, f"Incompatible types for expression.elem_type: {type(op1)}, {type(op2)}")

            elif(self.type_check(op1, op2, [str], expression.elem_type, False)):
                match (expression.elem_type):
                    case "==": return op1 == op2
                    case "!=": return op1 != op2
                    case "+" : return op1 + op2
                    case "_" : super().error(ErrorType.TYPE_ERROR, f"Incompatible types for expression.elem_type: {type(op1)}, {type(op2)}")
                
            
            elif(expression.elem_type == "=="):
                if(type(op1) == type(op2)): return op1 == op2
                return False 
            elif(expression.elem_type == "!="):
                if(type(op1) == type(op2)): return op1 != op2
                return True 
            
            super().error(ErrorType.TYPE_ERROR, f"Incompatible types for {expression.elem_type}: {type(op1)}, {type(op2)}")
        

        # Single operand operation
        elif(expression.elem_type in ["!", "neg"]):
            op1 = self.get_expression_value(expression.dict["op1"], scope_env)
            if(expression.elem_type == "!"):
                self.type_check_unary(op1, [bool], "unary boolean negation", True)
                return (not op1)
            if(expression.elem_type == "neg"):
                self.type_check_unary(op1, [int], "unary integer negation", True)
                return -op1
            
            super().error(ErrorType.TYPE_ERROR, f"Incompatible type for {expression.elem_type}: {type(op1)}")

        elif(expression.elem_type == "fcall"):
            return self.exec_func(expression.dict["name"], expression.dict["args"], scope_env)
        
        super().error(ErrorType.NAME_ERROR, f"Undefined expression type: {expression.elem_type}, Op1: {type(op1)}, Op2: {type(op2)}")

    def exec_func(self, func_name, args, scope_env):
        if(func_name == "print"):
            output_string = ""
            for item in args:
                arg_val = self.get_expression_value(item, scope_env)
                if(arg_val == None):
                    output_string += "nil"
                elif(type(arg_val) == bool):
                    if(arg_val): output_string  += "true"
                    else: output_string += "false"
                elif(type(arg_val) == tuple and arg_val[0] == RAISE):
                    return arg_val
                else:
                    output_string += str(arg_val)
            super().output(output_string)
            return None
        
        if(func_name == "inputi"):
            if(len(args) > 1):
                super().error(ErrorType.NAME_ERROR, "No inputi function takes > 1 parameters")
            if(len(args) == 1):
                prompt = self.get_expression_value(args[0], scope_env)
                super().output(prompt)
            user_input = super().get_input()
            try:
                return int(user_input)
            except ValueError:
                return user_input

        if(func_name == "inputs"):
            if(len(args) > 1):
                super().error(ErrorType.NAME_ERROR, "No inputi function takes > 1 parameters")
            if(len(args) == 1):
                super().output(self.get_expression_value(args[0], scope_env))
            user_input =super().get_input()
            if(type(user_input) == str):
                return user_input
            super().error(ErrorType.TYPE_ERROR, f"Invalid user input return type: {type(user_input)}")
            
        
        f_signature = (func_name, len(args))
        if (f_signature in self.func_dict.keys()):
            return self.get_expression_value(self.run_func(self.func_dict[f_signature], args), scope_env)

        super().error(ErrorType.NAME_ERROR, f"No function of name '{func_name}' with {len(args)} arguments exists")


def main():
    test_num = -1
    testing = testFramework()
    interpreter = Interpreter()
    if(test_num == "all"):

        for i in range(len(testing.testPrograms)):
            test = testing.testPrograms[i]
            print(f"\n\n------------\nRunning test #{i}\n--------------")
            
            try:
                interpreter.run(test)
                print(f"Test case {i} successfully ran")
            except:
                print(f"Test case {i} failed!")
    else:
        program_txt = testing.testPrograms[test_num]
        interpreter = Interpreter()
        interpreter.run(program_txt)

main()