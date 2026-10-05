# Brief 005: Versions/milestones and time tracking (extension)

Map a feature to an OpenProject version (create if missing, after confirmation) and assign its work packages. Command `speckit.openproject.log-time` logs time entries on work packages (activity from `list_time_entry_activities`) from user-supplied durations. Acceptance: version created once, WPs assigned, time entries created with correct activity and hours, all idempotent via ledger.
