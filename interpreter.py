import unittest  # Run unit tests with $ python3 -m unittest interpreter
import random


def list_singleton(maybe_list):
    """
    To make everything into a list, without making the lists too deep.
    """
    if isinstance(maybe_list, list):
        return maybe_list
    else:
        return [maybe_list]


class Interpreter:
    """
        Recursively interprets a tree of instructions (comprised of functions)
        This is all going to seem a little strange if you don't understand lazy evaluation.

    """

    @staticmethod
    def execute_expression(expr):
        # Instructions are in a tree, should be able to recursively handle it
        [action_fn, *args] = list_singleton(expr)

        if len(args) == 0:
            return action_fn
        elif len(args) > 0:
            # Evaluate the arguments
            argvals = [Interpreter.execute_expression(arg) for arg in args]

            # Return a lazy computed value
            return lambda: action_fn(*argvals)
        return lambda: 0


class CodeGenerator:
    def __init__(self):
        self.define_language()

    @staticmethod
    def checked_divide(a, b):
        val_b = b()
        val_a = a()

        if val_b <= 0:
            return 0
        else:
            return val_a / val_b

    def define_language(self):
        """
        Define the set of available isntructions using lambda functions.

        Please note that *everything is a function*, even constant values. This comes
        with two main advantages:
            1. The interpreter becomes much more simple as it is only dealing with one 
               type of data
            2. It allows us to use "lazy evaluation", which means that the macros (as 
               described in the GE class on the 24th feb) are nothing special, because
               each functional node is forced to decide if it wants to evaluate each 
               subtree or not.
        """
        def pront(string):
            def __internal(value):
                print(string, value())
                return value()
            return __internal



        self.terminal_nodes = [
            ("0", lambda: 0),
            ("1", lambda: 1),
            ("2", lambda: 2),
            ("3", lambda: 3),
            ("4", lambda: 4),
            ("5", lambda: 5),
            ("6", lambda: 6),
            ("7", lambda: 7),
            ("8", lambda: 8),
            ("9", lambda: 9),
            ("10", lambda: 10)
        ]

        self.function_nodes = [
            ("+", lambda a, b: a() + b()),
            ("-", lambda a, b: a() - b()),
            ("*", lambda a, b: a() * b()),
            ("/", CodeGenerator.checked_divide),
            ("if", lambda cond, a, b: a() if cond else b()),
            ("id", lambda a: a()),
        ]


    def _gen_random_expression(self, function_set, terminal_nodes, max_depth):
        if max_depth == 0:
            expr = [random.choice(terminal_nodes)]
        else:
            name, fn = random.choice(function_set)

            args = []
            for i in range(fn.__code__.co_argcount):
                args.append(
                    self._gen_random_expression(
                        function_set,
                        terminal_nodes,
                        max_depth - 1))

            expr = [(name, fn)] + args

        return expr

    @staticmethod
    def _make_executable(expr):
        [(_, fn), *args] = expr

        if len(args) > 0:
            return [fn] + [CodeGenerator._make_executable(arg) for arg in args]
        else:
            return [fn]

    def _make_humanreadable(expr):
        [(name, _), *args] = expr

        if len(args) > 0:
            return [name] + [CodeGenerator._make_humanreadable(arg) for arg in args]
        else:
            return [name]

    def test(self):
        exprs = self._gen_random_expression(
            self.function_nodes,
            self.terminal_nodes,
            4)
        result = Interpreter.execute_expression(CodeGenerator._make_executable(exprs))()

        print(CodeGenerator._make_humanreadable(exprs), result)
        return result



class CodegenUnitTests(unittest.TestCase):
    def test_smoke_tests(self):

        cg = CodeGenerator()

        # it should be able to run a few thousand random evaluations without
        # any runtime issues
        for i in range(10000):
            cg.test()

        self.assertNotEqual(5, 2 + 2)

    def test_simple_expressions_are_evaluated_correctly(self):
        interpreter = Interpreter()
        expr1 = [
            lambda a, b: a() + b(),
            lambda: 2,
            lambda: 3
        ]
        self.assertEqual(5, interpreter.execute_expression(expr1)())

        expr2 = [
            lambda a: a()**2,
            lambda: 5
        ]
        self.assertEqual(25, interpreter.execute_expression(expr2)())

        expr3 = [
            lambda a, b: a() + b(),
            lambda: 2,
                [
                    lambda a: a()**2,
                    lambda: 5
            ]
        ]
        self.assertEqual(27, interpreter.execute_expression(expr3)())

    def test_cant_divide_by_zero_and_kill_everything(self):
        """Checks that we can't kill the program by erroring when dividing by 0"""

        expr = [
                CodeGenerator.checked_divide,
                lambda: 10,
                lambda: 0,
                ]

        result = Interpreter.execute_expression(expr)()

        self.assertEqual(0, result)

    def test_checked_divide_works(self):
        """Checks that the program still works when not dividing by 0"""

        expr = [
                CodeGenerator.checked_divide,
                lambda: 10,
                lambda: 2,
                ]

        result = Interpreter.execute_expression(expr)()

        self.assertEqual(5, result)

    def test_failing_if_conditions_are_not_executed(self):
        """Checks the lazy evaluation of impure functions passed to conditional functions"""
        interpreter = Interpreter()

        def conditional(i, a, b): return (a() if i() != 50 else b())

        state = {"calledA": False, "calledB": False, "calledCondition": False}

        def fnA(state):
            state()["calledA"] = True
            return 20

        def fnB(state):
            state()["calledB"] = True
            return 40

        def conditionFn(state):
            state()["calledCondition"] = True
            return 10

        expr = [
            conditional,
            [
                conditionFn,
                lambda: state
            ],
            [fnA,
             lambda: state
             ],
            [fnB,
             lambda: state
             ]
        ]

        self.assertEqual(20, interpreter.execute_expression(expr)())
        self.assertTrue(state['calledA'])
        self.assertTrue(state['calledCondition'])
        self.assertFalse(state['calledB'])
