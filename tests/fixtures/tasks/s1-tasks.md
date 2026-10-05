<!-- Scenario S1 fixture. Expected plan: 1 feature + 3 phases + 10 tasks = 14 items, no relations. -->
# Tasks: Sandbox Demo

## Phase 1: Setup

- [ ] T001 Create project skeleton in src/app/__init__.py
- [ ] T002 [P] Add configuration loader in src/app/config.py
- [ ] T003 [P] Add logging setup in src/app/log.py

## Phase 2: Core

- [ ] T004 [US1] Implement parser in src/app/parser.py
- [ ] T005 [US1] Implement renderer in src/app/render.py
- [ ] T006 [P] [US2] Add CLI entry point in src/app/cli.py
- [ ] T007 [US2] Wire CLI to parser in src/app/cli.py

## Phase 3: Polish

- [ ] T008 [P] Write README in README.md
- [ ] T009 [P] Add usage examples in docs/examples.md
- [ ] T010 Final review of all docs in docs/
