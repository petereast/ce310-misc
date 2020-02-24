import unittest
import random


def list_singleton(maybe_list):
    if isinstance(maybe_list, list):
        return maybe_list
    else:
        return [maybe_list]


class CodeGenerator:
    def __init__(self):
        def pront(string):
            def __internal(value):
                print(string, value())
                return value()
            return __internal

        def checked_divide(a, b):
            val_b = b()
            val_a = a()

            return val_a / val_b if val_b > 0 else 0

        # Define the "language" - the key of the dict is not used at the moment,
        # it's there to eventually support parsing the language? Maybe?  I'll
        # probably end up taking it out though
        # If I was writing this class for a production system, I these values
        # would be passed into the constructor

        self.terminal_nodes = dict([
            # Able to use thes 0-arity functions to fetch variables at runtime
            ("const1", lambda: 1),
            ("const2", lambda: 2),
            ("const3", lambda: 3)
        ])

        self.function_nodes = dict([
            # All values are functions - lazy execution
            ("+", lambda a, b: a() + b()),
            ("-", lambda a, b: a() - b()),
            ("*", lambda a, b: a() * b()),
            ("/", checked_divide),  # TODO: implement checked divide
            ("if", lambda cond, a, b: a() if cond else b()),
            ("id", lambda a: a()),
            # ("pront", pront("debug!"))
        ])

    def _choose_random(_, l):
        return random.choice(l)

    def _gen_random_expression(self, function_set, terminal_nodes, max_depth):
        if max_depth == 0:
            expr = [self._choose_random(terminal_nodes)]
        else:
            fn = self._choose_random(function_set)

            args = []
            for i in range(fn.__code__.co_argcount):
                args.append(
                    self._gen_random_expression(
                        function_set,
                        terminal_nodes,
                        max_depth - 1))

            expr = [fn] + args
        return expr

    def test(self):
        exprs = self._gen_random_expression(
            list(self.function_nodes.values()),
            list(self.terminal_nodes.values()),
            3)

        return self.execute_expression(exprs)()

    def execute_expression(self, expr):
        # Instructions are in a tree, should be able to recursively handle it
        [action_fn, *args] = list_singleton(expr)

        if len(args) == 0:
            return action_fn
        elif len(args) > 0:
            # Evaluate the arguments
            argvals = [self.execute_expression(arg) for arg in args]

            # Return a lazy computed value
            return lambda: action_fn(*argvals)
        return lambda: 0


class CodegenUnitTests(unittest.TestCase):
    def test_smoke_tests(self):

        cg = CodeGenerator()

        # it should be able to run a few thousand random evaluations without
        # any runtime issues
        for i in range(10000):
            cg.test()

        self.assertNotEqual(5, 2 + 2)

    def test_simple_expressions_are_evaluated_correctly(self):
        cg = CodeGenerator()
        expr1 = [
            lambda a, b: a() + b(),
            lambda: 2,
            lambda: 3
        ]
        self.assertEqual(5, cg.execute_expression(expr1)())

        expr2 = [
            lambda a: a()**2,
            lambda: 5
        ]
        self.assertEqual(25, cg.execute_expression(expr2)())

        expr3 = [
            lambda a, b: a() + b(),
            lambda: 2,
                [
                    lambda a: a()**2,
                    lambda: 5
            ]
        ]
        self.assertEqual(27, cg.execute_expression(expr3)())

    def test_failing_if_conditions_are_not_executed(self):
        """Checks the lazy evaluation of impure functions passed to conditional functions"""
        cg = CodeGenerator()

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

        self.assertEqual(20, cg.execute_expression(expr)())
        self.assertTrue(state['calledA'])
        self.assertTrue(state['calledCondition'])
        self.assertFalse(state['calledB'])
