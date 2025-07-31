from ....predicate import Predicate

class YFix(Predicate):
    def __init__(self, predicate: Predicate):
        self._predicate = predicate

    def __getattr__(self, attr):
        # Use object.__getattribute__ to avoid infinite recursion
        _predicate = object.__getattribute__(self, '_predicate')
        return getattr(_predicate, attr)
    
    def preval(self, annotated=False):
        """Evaluate the YFix object."""
        # Call the preval method of the underlying predicate
        return self._predicate.preval(annotated=annotated)
