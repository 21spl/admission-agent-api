# app/ai/validation/cross_match.py

from dataclasses import dataclass, field


@dataclass
class CrossMatchResult:
    flags: int = 0
    issues: list[str] = field(default_factory=list)

    def add(self, issue: str) -> None:
        self.flags += 1
        self.issues.append(issue)

    @property
    def issues_string(self) -> str:
        return ", ".join(self.issues)


def _normalize_name(name: str | None) -> str:
    if not name:
        return ""
    return " ".join(name.strip().lower().split())


def _names_match(a: str | None, b: str | None) -> bool:
    norm_a, norm_b = _normalize_name(a), _normalize_name(b)
    if not norm_a or not norm_b:
        return True  # nothing to compare, skip
    return norm_a == norm_b


def _dates_match(a, b) -> bool:
    if not a or not b:
        return True  # nothing to compare, skip
    return str(a) == str(b)


def cross_match_documents(
    marksheet: dict,
    id_card: dict,
    registration_name: str | None,
    registration_dob,
) -> CrossMatchResult:
    """Compares extracted marksheet + ID fields against each other and
    against the student's registration record."""
    result = CrossMatchResult()

    marksheet_name = marksheet.get("student_name")
    id_name = id_card.get("full_name")
    marksheet_dob = marksheet.get("dob")
    id_dob = id_card.get("dob")

    if not _names_match(marksheet_name, id_name):
        result.add("name mismatch between marksheet and ID")
    if not _names_match(registration_name, marksheet_name):
        result.add("name mismatch between application and marksheet")
    if not _names_match(registration_name, id_name):
        result.add("name mismatch between application and ID")

    if not _dates_match(marksheet_dob, id_dob):
        result.add("dob mismatch between marksheet and ID")
    if not _dates_match(registration_dob, id_dob):
        result.add("dob mismatch between application and ID")
    if not _dates_match(registration_dob, marksheet_dob):
        result.add("dob mismatch between application and marksheet")

    return result
