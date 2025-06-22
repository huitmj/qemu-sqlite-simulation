from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid as uuid_lib

class RequestStatus(str, Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RUNNING = "running"
    CANCELLED = "cancelled"
    HOLD = "hold"
    DONE = "done"

class LogType(str, Enum):
    BOOT = "boot"
    COMMAND = "command"
    STDOUT = "stdout"
    STDERR = "stderr"

class RequestCreate(BaseModel):
    vm_name: str
    commands: str
    timeout: int = Field(default=5, ge=1)

class Request(BaseModel):
    uuid: str
    vm_name: str
    commands: str
    timeout: int
    created_at: datetime
    updated_at: datetime
    status: RequestStatus
    
    @classmethod
    def create_new(cls, vm_name: str, commands: str, timeout: int = 5) -> 'Request':
        now = datetime.now()
        return cls(
            uuid=str(uuid_lib.uuid4()),
            vm_name=vm_name,
            commands=commands,
            timeout=timeout,
            created_at=now,
            updated_at=now,
            status=RequestStatus.PENDING
        )

class WorkLogEntry(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    output: str
    log_type: LogType

class RequestResponse(BaseModel):
    uuid: str
    status: RequestStatus
    message: str

class WorkLogResponse(BaseModel):
    request_uuid: str
    logs: List[WorkLogEntry]
    total_entries: int