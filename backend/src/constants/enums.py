from enum import StrEnum
class Role(StrEnum):
 ADMIN="admin"
 ANALYST="analyst"
 VIEWER="viewer"
class RunStatus(StrEnum):
 QUEUED="queued"
 RUNNING="running"
 COMPLETED="completed"
 FAILED="failed"
class RangeBand(StrEnum):
 LOW="low"
 MIDDLE="middle"
 HIGH="high"
UNITS=["kPa","bar","degC","mg/L"]
