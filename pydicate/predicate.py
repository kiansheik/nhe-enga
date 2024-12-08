from copy import deepcopy

class Predicate:
    def __init__(self, verbete, category, min_args, max_args=None):
        """
        Initialize a Predicate object.
        :param verbete: The core lexeme or word root.
        :param category: The linguistic category (e.g., 'verb', 'noun').
        :param min_args: Minimum number of required arguments.
        :param max_args: Maximum number of arguments (default: same as min_args; None for unlimited).
        """
        self.verbete = verbete
        self.category = category
        self.min_args = min_args
        self.max_args = max_args if max_args is not None else min_args
        self.arguments = []
        self.adjuncts = []

    def copy(self):
        """
        Create a deep copy of the predicate.
        :return: A deep copy of the predicate.
        """
        return deepcopy(self)
    
    def __mul__(self, other):
        """
        Add an argument using the * operator.
        :param other: The argument to add.
        :return: Self (to enable chaining).
        """
        if self.max_args is not None and len(self.arguments) >= self.max_args:
            raise ValueError(f"Cannot add more arguments. Max arguments ({self.max_args}) reached.")
        mult = self.copy()
        other_copy = other.copy()
        mult.arguments.append(other_copy)
        return mult

    def __add__(self, other):
        """
        Add an adjunct using the + operator.
        :param other: The adjunct to add.
        :return: Self (to enable chaining).
        """
        mult = self.copy()
        other_copy = other.copy()
        mult.adjuncts.append(other_copy)
        return mult

    def is_valid(self):
        """
        Check if the predicate has a valid number of arguments.
        :return: True if the number of arguments is within the min/max range, False otherwise.
        """
        return len(self.arguments) >= self.min_args

    def __repr__(self):
        args = ", ".join(repr(arg) for arg in self.arguments)
        adjuncts = ", ".join(repr(adj) for adj in self.adjuncts)
        return (f"Predicate(verbete={self.verbete}, category={self.category}, "
                f"arguments=[{args}], adjuncts=[{adjuncts}], "
                f"min_args={self.min_args}, max_args={self.max_args})")

    def eval(self):
        """
        Evaluate the predicate by applying the arguments and adjuncts.
        Default response: f"{self.verbete}(args...) + adjunct1 + adjunct2 + ..."
        :return: The result of applying the predicate.
        """
        args = ", ".join(arg.eval() for arg in self.arguments)
        adjuncts = " + ".join(adj.eval() for adj in self.adjuncts) if self.adjuncts else ""
        repr = f"{self.verbete}"
        args_repr = f"{repr}({args})" if args else repr
        return f"{args_repr} + {adjuncts}" if adjuncts else args_repr
    
    # def __str__(self):
    #     return self.eval()
