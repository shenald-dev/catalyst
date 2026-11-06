from catalyst.domain.engine import _resolve_call_args


def test_resolve_call_args_no_sig() -> None:
    call_args, call_kwargs = _resolve_call_args(123, ["A"], {"A": 1})  # type: ignore
    assert call_args == ()
    assert call_kwargs == {}

def test_resolve_call_args_positional_only() -> None:
    def my_func(a: int, /) -> None:
        pass

    call_args, call_kwargs = _resolve_call_args(my_func, ["A"], {"A": 1})
    assert call_args == (1,)
    assert call_kwargs == {}

def test_resolve_call_args_dict_injection() -> None:
    def my_func(context: dict[str, int]) -> None:
        pass

    _call_args, call_kwargs = _resolve_call_args(my_func, ["A", "B"], {"A": 1, "B": 2, "C": 3})
    assert call_kwargs == {"context": {"A": 1, "B": 2}}

def test_resolve_call_args_dict_injection_positional_only() -> None:
    def my_func(inputs: dict[str, int], /) -> None:
        pass

    call_args, _call_kwargs = _resolve_call_args(my_func, ["A", "B"], {"A": 1, "B": 2, "C": 3})
    assert call_args == ({"A": 1, "B": 2},)

def test_resolve_call_args_has_var_positional_with_positional_or_keyword_and_context() -> None:
    def my_func(context: dict[str, int], *args: int) -> None:
        pass

    call_args, _call_kwargs = _resolve_call_args(my_func, ["A", "B"], {"A": 1, "B": 2, "C": 3})
    assert call_args == ({"A": 1, "B": 2}, 1, 2)

def test_resolve_call_args_var_positional_with_positional_or_keyword_and_match() -> None:
    def my_func(B: int, *args: int) -> None:
        pass

    call_args, _call_kwargs = _resolve_call_args(my_func, ["A", "B"], {"A": 1, "B": 2})
    assert call_args == (2, 1)
