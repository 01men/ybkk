"""V2 verify 棒自测 runner（无 pytest 时使用）。

直接 import + 调用 test_llm_judge 里的所有测试函数，统计 pass/fail。
"""
from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path


def run_module_tests(module_name: str, project_root: str) -> tuple[int, int, list[str]]:
    """导入一个含测试函数的模块，跑每个 test_ 前缀函数。

    返回 (passed, failed, failed_names)
    """
    sys.path.insert(0, project_root)
    mod = importlib.import_module(module_name)

    # 收集模块内 @pytest.fixture 函数（无 request param 的）
    fixtures: dict[str, callable] = {}
    try:
        import pytest  # type: ignore
    except ImportError:
        pytest = None  # type: ignore
    if pytest is not None:
        # 暴力扫：拿 module 字典里的所有 callable
        scan_target = getattr(mod, "__dict__", {})
        for name in list(scan_target.keys()):
            obj = scan_target[name]
            cls_name = type(obj).__name__ if obj is not None else ""
            is_fixture = (
                hasattr(obj, "_pytestfixturefunction")
                or cls_name == "FixtureFunctionDefinition"
            )
            if is_fixture:
                inner = None
                for attr in ("func", "_fixturefunction", "__wrapped__"):
                    cand = getattr(obj, attr, None)
                    if callable(cand):
                        inner = cand
                        break
                if inner is None:
                    inner = obj
                fixtures[name] = inner

    passed = 0
    failed = 0
    failed_names: list[str] = []
    import inspect
    for name in dir(mod):
        if not name.startswith("test_"):
            continue
        fn = getattr(mod, name)
        if not callable(fn):
            continue
        try:
            sig = inspect.signature(fn)
            kwargs = {}
            for pname, param in sig.parameters.items():
                if pname in fixtures:
                    kwargs[pname] = fixtures[pname]()
            if inspect.iscoroutinefunction(fn):
                import asyncio
                asyncio.run(fn(**kwargs))
            else:
                fn(**kwargs)
            passed += 1
            print(f"  PASS  {name}")
        except Exception as e:
            failed += 1
            failed_names.append(name)
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
    return passed, failed, failed_names


def main():
    total_p, total_f, all_failed = 0, 0, []
    for mod_name, src_root, tests_root in [
        ("test_llm_judge", "apps/flow_engine/src", "apps/flow_engine/tests"),
        ("test_parsers", "apps/ingest/src", "apps/ingest/tests"),
        ("test_mapping", "apps/ontology/src", "apps/ontology/tests"),
        ("test_schema", "apps/ontology/src", "apps/ontology/tests"),
    ]:
        print(f"\n=== {mod_name} (src={src_root} tests={tests_root}) ===")
        # 先把 src 放到 sys.path（让 aios_flow.* 可解析），再把 tests 放到 sys.path
        sys.path.insert(0, str(Path(src_root).resolve()))
        sys.path.insert(0, str(Path(tests_root).resolve()))
        p, f, fns = run_module_tests(mod_name, src_root)
        total_p += p
        total_f += f
        all_failed.extend(fns)
    print(f"\n=== TOTAL: {total_p} passed, {total_f} failed ===")
    if all_failed:
        print(f"Failed: {all_failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
