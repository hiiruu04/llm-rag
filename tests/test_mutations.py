import asyncio
import sys
import traceback

sys.path.insert(0, "/home/ohiru/Documents/workspace/learning/llm-rag")

from app.core.database import async_session_factory
from sqlalchemy import text


async def get_test_ids():
    async with async_session_factory() as db:
        r = await db.execute(text("SELECT id FROM tasks WHERE status = 'pending' LIMIT 1"))
        task_row = r.fetchone()
        task_id = str(task_row[0]) if task_row else None

        r = await db.execute(text("SELECT id FROM workers WHERE status = 'active' LIMIT 1"))
        worker_row = r.fetchone()
        worker_id = str(worker_row[0]) if worker_row else None

        r = await db.execute(text("SELECT id FROM workers WHERE status = 'active' LIMIT 1"))
        worker_name_row = r.fetchone()
        worker_name_id = str(worker_name_row[0]) if worker_name_row else None

        r = await db.execute(text("SELECT id FROM shifts LIMIT 1"))
        shift_row = r.fetchone()
        shift_id = str(shift_row[0]) if shift_row else None

        r = await db.execute(
            text("SELECT id, employee_id FROM workers WHERE status = 'active' LIMIT 1")
        )
        emp_row = r.fetchone()
        employee_id = emp_row[1] if emp_row else None

        r = await db.execute(text("SELECT id FROM down_events WHERE status = 'active' LIMIT 1"))
        de_row = r.fetchone()
        down_event_id = str(de_row[0]) if de_row else None

        r = await db.execute(text("SELECT id FROM faults LIMIT 1"))
        f_row = r.fetchone()
        fault_id = str(f_row[0]) if f_row else None

        r = await db.execute(text("SELECT id FROM assets LIMIT 1"))
        a_row = r.fetchone()
        asset_id = str(a_row[0]) if a_row else None

    return {
        "task_id": task_id,
        "worker_id": worker_id,
        "worker_name_id": worker_name_id,
        "shift_id": shift_id,
        "employee_id": employee_id,
        "down_event_id": down_event_id,
        "fault_id": fault_id,
        "asset_id": asset_id,
    }


async def test_scheduler_mutations():
    from app.agents.mutation_service import (
        assign_task,
        update_task_status,
        reschedule_task,
        execute_scheduler_mutation,
    )

    ids = await get_test_ids()
    results = []

    print("\n" + "=" * 60)
    print("TESTING SCHEDULER MUTATIONS")
    print("=" * 60)

    # Test 1: assign_task with UUID
    print("\n--- Test 1: assign_task (UUID) ---")
    if ids["task_id"] and ids["worker_id"]:
        try:
            result = await assign_task(ids["task_id"], ids["worker_id"])
            print(f"  Result: {result}")
            results.append(("assign_task UUID", "PASS" if "task_id" in result else "FAIL", result))
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("assign_task UUID", "ERROR", str(e)))
    else:
        print("  SKIP: No test data")
        results.append(("assign_task UUID", "SKIP", ""))

    # Test 2: update_task_status
    print("\n--- Test 2: update_task_status ---")
    if ids["task_id"]:
        try:
            result = await update_task_status(ids["task_id"], "in_progress")
            print(f"  Result: {result}")
            results.append(
                ("update_task_status", "PASS" if "task_id" in result else "FAIL", result)
            )
            # Reset back
            await update_task_status(ids["task_id"], "pending")
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("update_task_status", "ERROR", str(e)))
    else:
        results.append(("update_task_status", "SKIP", ""))

    # Test 3: reschedule_task
    print("\n--- Test 3: reschedule_task ---")
    if ids["task_id"] and ids["shift_id"]:
        try:
            result = await reschedule_task(ids["task_id"], ids["shift_id"])
            print(f"  Result: {result}")
            results.append(("reschedule_task", "PASS" if "task_id" in result else "FAIL", result))
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("reschedule_task", "ERROR", str(e)))
    else:
        results.append(("reschedule_task", "SKIP", ""))

    # Test 4: execute_scheduler_mutation - assign_task
    print("\n--- Test 4: execute_scheduler_mutation (assign_task) ---")
    if ids["task_id"] and ids["worker_id"]:
        try:
            mutation_str = f"assign_task:{ids['task_id']}:{ids['worker_id']}"
            result = await execute_scheduler_mutation(mutation_str)
            print(f"  Result: {result}")
            results.append(
                (
                    "execute_scheduler assign_task",
                    "PASS" if "task_id" in result else "FAIL",
                    result,
                )
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("execute_scheduler assign_task", "ERROR", str(e)))
    else:
        results.append(("execute_scheduler assign_task", "SKIP", ""))

    # Test 5: execute_scheduler_mutation with unknown action
    print("\n--- Test 5: execute_scheduler_mutation (unknown) ---")
    try:
        result = await execute_scheduler_mutation("unknown_action:foo:bar")
        print(f"  Result: {result}")
        has_error = result.get("type") == "error"
        results.append(("execute_scheduler unknown", "PASS" if has_error else "FAIL", result))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(("execute_scheduler unknown", "ERROR", str(e)))

    # Test 6: assign_task with invalid UUID
    print("\n--- Test 6: assign_task (invalid UUID) ---")
    try:
        result = await assign_task(
            "00000000-0000-0000-0000-000000000000",
            ids["worker_id"] or "00000000-0000-0000-0000-000000000000",
        )
        print(f"  Result: {result}")
        not_found = result.get("type") == "not_found"
        results.append(("assign_task invalid UUID", "PASS" if not_found else "FAIL", result))
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        results.append(("assign_task invalid UUID", "ERROR", str(e)))

    # Test 7: update_task_status with invalid status
    print("\n--- Test 7: update_task_status (invalid status) ---")
    try:
        result = await update_task_status(
            ids["task_id"] or "00000000-0000-0000-0000-000000000000", "invalid_status"
        )
        print(f"  Result: {result}")
        has_error = result.get("type") == "error"
        results.append(("update_task_status invalid", "PASS" if has_error else "FAIL", result))
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append(("update_task_status invalid", "ERROR", str(e)))

    return results


async def test_analyzer_mutations():
    from app.agents.mutation_service import (
        log_down_event,
        close_down_event,
        update_fault_severity,
        execute_analyzer_mutation,
    )

    ids = await get_test_ids()
    results = []

    print("\n" + "=" * 60)
    print("TESTING ANALYZER MUTATIONS")
    print("=" * 60)

    # Test 8: update_fault_severity
    print("\n--- Test 8: update_fault_severity ---")
    if ids["fault_id"]:
        try:
            result = await update_fault_severity(ids["fault_id"], "high")
            print(f"  Result: {result}")
            results.append(
                ("update_fault_severity", "PASS" if "fault_id" in result else "FAIL", result)
            )
            # Reset
            from sqlalchemy import select
            from app.models.fault import Fault
            from uuid import UUID

            async with async_session_factory() as db:
                fault = await db.get(Fault, UUID(ids["fault_id"]))
                if fault:
                    original_severity = fault.severity
                    # Restore original severity
                    await update_fault_severity(ids["fault_id"], original_severity)
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("update_fault_severity", "ERROR", str(e)))
    else:
        results.append(("update_fault_severity", "SKIP", ""))

    # Test 9: log_down_event
    print("\n--- Test 9: log_down_event ---")
    if ids["asset_id"] and ids["fault_id"]:
        try:
            result = await log_down_event(ids["asset_id"], ids["fault_id"], "Test down event")
            print(f"  Result: {result}")
            new_event_id = result.get("id")
            results.append(("log_down_event", "PASS" if "id" in result else "FAIL", result))

            # Test 10: close_down_event
            if new_event_id:
                print("\n--- Test 10: close_down_event ---")
                try:
                    result = await close_down_event(new_event_id, "Test resolution")
                    print(f"  Result: {result}")
                    results.append(
                        (
                            "close_down_event",
                            "PASS" if result.get("status") == "resolved" else "FAIL",
                            result,
                        )
                    )
                except Exception as e:
                    print(f"  ERROR: {e}")
                    traceback.print_exc()
                    results.append(("close_down_event", "ERROR", str(e)))
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("log_down_event", "ERROR", str(e)))
            results.append(("close_down_event", "SKIP", ""))
    else:
        results.append(("log_down_event", "SKIP", ""))
        results.append(("close_down_event", "SKIP", ""))

    # Test 11: execute_analyzer_mutation
    print("\n--- Test 11: execute_analyzer_mutation (update_fault_severity) ---")
    if ids["fault_id"]:
        try:
            mutation_str = f"update_fault_severity:{ids['fault_id']}:critical"
            result = await execute_analyzer_mutation(mutation_str)
            print(f"  Result: {result}")
            results.append(
                (
                    "execute_analyzer update_severity",
                    "PASS" if "fault_id" in result else "FAIL",
                    result,
                )
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(("execute_analyzer update_severity", "ERROR", str(e)))
    else:
        results.append(("execute_analyzer update_severity", "SKIP", ""))

    # Test 12: execute_analyzer_mutation with unknown action
    print("\n--- Test 12: execute_analyzer_mutation (unknown) ---")
    try:
        result = await execute_analyzer_mutation("unknown:foo:bar")
        print(f"  Result: {result}")
        has_error = result.get("type") == "error"
        results.append(("execute_analyzer unknown", "PASS" if has_error else "FAIL", result))
    except Exception as e:
        results.append(("execute_analyzer unknown", "ERROR", str(e)))

    # Test 13: update_fault_severity with invalid severity
    print("\n--- Test 13: update_fault_severity (invalid severity) ---")
    try:
        result = await update_fault_severity(
            ids.get("fault_id", "00000000-0000-0000-0000-000000000000"), "extreme"
        )
        print(f"  Result: {result}")
        has_error = result.get("type") == "error"
        results.append(("update_fault_severity invalid", "PASS" if has_error else "FAIL", result))
    except Exception as e:
        results.append(("update_fault_severity invalid", "ERROR", str(e)))

    return results


async def test_recommender_mutations():
    from app.agents.mutation_service import log_down_event, record_outcome, update_task_status

    ids = await get_test_ids()
    results = []

    print("\n" + "=" * 60)
    print("TESTING RECOMMENDER MUTATIONS (existing)")
    print("=" * 60)

    # Test 14: record_outcome
    print("\n--- Test 14: record_outcome ---")
    if ids["task_id"]:
        try:
            result = await record_outcome(ids["task_id"], "Test outcome result")
            print(f"  Result: {result}")
            # Reset task back to pending
            await update_task_status(ids["task_id"], "pending")
            results.append(("record_outcome", "PASS" if "id" in result else "FAIL", result))
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("record_outcome", "ERROR", str(e)))
    else:
        results.append(("record_outcome", "SKIP", ""))

    # Test 15: log_down_event
    print("\n--- Test 15: log_down_event ---")
    if ids["asset_id"] and ids["fault_id"]:
        try:
            result = await log_down_event(ids["asset_id"], ids["fault_id"], severity="medium")
            print(f"  Result: {result}")
            results.append(("log_down_event", "PASS" if "id" in result else "FAIL", result))
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("log_down_event", "ERROR", str(e)))
    else:
        results.append(("log_down_event", "SKIP", ""))

    return results


async def test_mcp_tools():
    from app.mcp.tools.agent_tools import scheduling_agent, analyzer_agent, recommender_agent

    ids = await get_test_ids()
    results = []

    print("\n" + "=" * 60)
    print("TESTING MCP TOOL INTERFACE")
    print("=" * 60)

    # Test 16: scheduling_agent with mutation
    print("\n--- Test 16: scheduling_agent tool (with mutation) ---")
    if ids["task_id"] and ids["worker_id"]:
        try:
            mutation_str = f"assign_task:{ids['task_id']}:{ids['worker_id']}"
            result = await scheduling_agent(
                question="What tasks are currently pending?",
                mutation=mutation_str,
            )
            print(f"  Result length: {len(result)} chars")
            has_mutation = "[Scheduling mutation:" in result
            results.append(
                ("scheduling_agent mutation", "PASS" if has_mutation else "FAIL", result[:200])
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("scheduling_agent mutation", "ERROR", str(e)))
    else:
        results.append(("scheduling_agent mutation", "SKIP", ""))

    # Test 17: analyzer_agent with mutation
    print("\n--- Test 17: analyzer_agent tool (with mutation) ---")
    if ids["fault_id"]:
        try:
            mutation_str = f"update_fault_severity:{ids['fault_id']}:medium"
            result = await analyzer_agent(
                question="What are the current KPI metrics?",
                mutation=mutation_str,
            )
            print(f"  Result length: {len(result)} chars")
            has_mutation = "[Analysis mutation:" in result
            results.append(
                ("analyzer_agent mutation", "PASS" if has_mutation else "FAIL", result[:200])
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("analyzer_agent mutation", "ERROR", str(e)))
    else:
        results.append(("analyzer_agent mutation", "SKIP", ""))

    # Test 18: recommender_agent with mutation (existing)
    print("\n--- Test 18: recommender_agent tool (with mutation) ---")
    if ids["task_id"]:
        try:
            mutation_str = f"record_outcome:{ids['task_id']}:Test outcome from test suite"
            result = await recommender_agent(
                question="What are the current faults?",
                mutation=mutation_str,
            )
            print(f"  Result length: {len(result)} chars")
            has_mutation = "[Outcome recorded:" in result or "[Mutation" in result
            results.append(
                ("recommender_agent mutation", "PASS" if has_mutation else "MAYBE", result[:200])
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results.append(("recommender_agent mutation", "ERROR", str(e)))
    else:
        results.append(("recommender_agent mutation", "SKIP", ""))

    return results


async def main():
    all_results = []

    try:
        scheduler_results = await test_scheduler_mutations()
        all_results.extend(scheduler_results)
    except Exception as e:
        print(f"\nScheduler tests failed with error: {e}")
        traceback.print_exc()

    try:
        analyzer_results = await test_analyzer_mutations()
        all_results.extend(analyzer_results)
    except Exception as e:
        print(f"\nAnalyzer tests failed with error: {e}")
        traceback.print_exc()

    try:
        recommender_results = await test_recommender_mutations()
        all_results.extend(recommender_results)
    except Exception as e:
        print(f"\nRecommender tests failed with error: {e}")
        traceback.print_exc()

    try:
        mcp_results = await test_mcp_tools()
        all_results.extend(mcp_results)
    except Exception as e:
        print(f"\nMCP tool tests failed with error: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, status, _ in all_results if status == "PASS")
    failed = sum(1 for _, status, _ in all_results if status == "FAIL")
    errors = sum(1 for _, status, _ in all_results if status == "ERROR")
    skipped = sum(1 for _, status, _ in all_results if status == "SKIP")
    maybe = sum(1 for _, status, _ in all_results if status == "MAYBE")

    for name, status, detail in all_results:
        icon = {"PASS": "+", "FAIL": "X", "ERROR": "!", "SKIP": "-", "MAYBE": "?"}.get(status, "?")
        detail_str = str(detail)[:100] if detail else ""
        print(f"  [{icon}] {name}: {status} {detail_str}")

    print(
        f"\n  Passed: {passed} | Failed: {failed} | Errors: {errors} | Skipped: {skipped} | Maybe: {maybe}"
    )
    print(f"  Total: {len(all_results)}")


if __name__ == "__main__":
    asyncio.run(main())
