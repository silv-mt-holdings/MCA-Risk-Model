"""
Letter Grader
=============
Convert numeric scores to letter grades.

Default Thresholds:
- A: 80-100 (Low Risk)
- B: 65-79 (Moderate Risk)
- C: 50-64 (Standard Risk)
- D: 35-49 (High Risk)
- F: 0-34 (Very High Risk)
"""

from dataclasses import dataclass
from typing import Dict, Optional
import json
from pathlib import Path


@dataclass
class LetterGrade:
    """Letter grade information"""
    grade: str
    min_score: float
    max_score: float
    risk_level: str
    description: str
    color: str = 'gray'


# Default grade thresholds
DEFAULT_GRADES = {
    'A': LetterGrade('A', 80, 100, 'Low Risk', 'Excellent - Approve', 'green'),
    'B': LetterGrade('B', 65, 79, 'Moderate Risk', 'Good - Approve with standard terms', 'lightgreen'),
    'C': LetterGrade('C', 50, 64, 'Standard Risk', 'Average - Review recommended', 'yellow'),
    'D': LetterGrade('D', 35, 49, 'High Risk', 'Below Average - Additional review required', 'orange'),
    'F': LetterGrade('F', 0, 34, 'Very High Risk', 'Poor - Decline recommended', 'red'),
}


def grade_from_score(score: float, grades: Dict[str, LetterGrade] = None) -> LetterGrade:
    """
    Convert numeric score to letter grade.

    Args:
        score: Numeric score (0-100)
        grades: Optional custom grade definitions

    Returns:
        LetterGrade object
    """
    grades = grades or DEFAULT_GRADES

    # Clamp score
    score = max(0, min(100, score))

    for grade_info in sorted(grades.values(), key=lambda g: g.min_score, reverse=True):
        if score >= grade_info.min_score:
            return grade_info

    return grades['F']


class LetterGrader:
    """
    Letter grade converter with configurable thresholds.

    Usage:
        grader = LetterGrader()
        grade = grader.grade(75)  # Returns 'B'
    """

    def __init__(self, config_path: str = None):
        self.grades = DEFAULT_GRADES.copy()

        if config_path:
            self._load_config(config_path)

    def _load_config(self, path: str):
        """Load grade thresholds from JSON config"""
        try:
            with open(path) as f:
                data = json.load(f)

            for grade, info in data.items():
                self.grades[grade] = LetterGrade(
                    grade=grade,
                    min_score=info['min_score'],
                    max_score=info['max_score'],
                    risk_level=info.get('risk_level', ''),
                    description=info.get('description', ''),
                    color=info.get('color', 'gray'),
                )
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

    def grade(self, score: float) -> str:
        """Get letter grade for score"""
        return grade_from_score(score, self.grades).grade

    def grade_info(self, score: float) -> LetterGrade:
        """Get full grade info for score"""
        return grade_from_score(score, self.grades)

    def is_passing(self, score: float) -> bool:
        """Check if score is passing (C or better)"""
        return score >= 50

    def get_thresholds(self) -> Dict:
        """Get current grade thresholds"""
        return {
            grade: {'min': info.min_score, 'max': info.max_score}
            for grade, info in self.grades.items()
        }
