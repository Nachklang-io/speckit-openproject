<!-- Scenario S4 fixture. Expected follows pairs (successor -> predecessor):
     T004 -> T002, T005 -> T004, T006 -> T001.
     Tasks marked [P] without a stated dependency (T001, T002, T003) get no relation between them. -->
# Tasks: Dependency Demo

## Phase 1: Foundation

- [ ] T001 [P] Create database schema in db/schema.sql
- [ ] T002 [P] Create API skeleton in src/api.py
- [ ] T003 [P] Create test harness in tests/harness.py

## Phase 2: Features

- [ ] T004 Implement endpoint in src/api.py (depends on T002)
- [ ] T005 Add endpoint tests in tests/test_api.py (depends on T004)
- [ ] T006 Add migration runner in db/migrate.py (depends on T001)

## Dependencies

- T004 depends on T002
- T005 depends on T004
- T006 depends on T001
