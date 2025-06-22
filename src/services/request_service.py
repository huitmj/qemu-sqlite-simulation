from fastapi import FastAPI, HTTPException
from typing import List, Optional
from datetime import datetime
import sqlite3

from ..database.connection import DatabaseConnection
from ..database.models import (
    Request, RequestCreate, RequestResponse, 
    RequestStatus, WorkLogResponse, WorkLogEntry
)

app = FastAPI(title="QEMU Simulation Request Service", version="1.0.0")

db = DatabaseConnection()

@app.post("/requests", response_model=RequestResponse)
async def create_request(request_data: RequestCreate):
    request = Request.create_new(
        vm_name=request_data.vm_name,
        commands=request_data.commands,
        timeout=request_data.timeout
    )
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO requests (uuid, vm_name, commands, timeout, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                request.uuid, request.vm_name, request.commands, request.timeout,
                request.created_at, request.updated_at, request.status.value
            ))
            conn.commit()
        
        db.create_work_log_table(request.uuid)
        
        return RequestResponse(
            uuid=request.uuid,
            status=request.status,
            message="Request created successfully"
        )
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/requests", response_model=List[Request])
async def get_all_requests(status: Optional[RequestStatus] = None):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM requests WHERE status = ? ORDER BY created_at DESC", (status.value,))
            else:
                cursor.execute("SELECT * FROM requests ORDER BY created_at DESC")
            
            rows = cursor.fetchall()
            
            requests = []
            for row in rows:
                requests.append(Request(
                    uuid=row['uuid'],
                    vm_name=row['vm_name'],
                    commands=row['commands'],
                    timeout=row['timeout'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    status=RequestStatus(row['status'])
                ))
            
            return requests
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/requests/{request_uuid}", response_model=Request)
async def get_request(request_uuid: str):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM requests WHERE uuid = ?", (request_uuid,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Request not found")
            
            return Request(
                uuid=row['uuid'],
                vm_name=row['vm_name'],
                commands=row['commands'],
                timeout=row['timeout'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                status=RequestStatus(row['status'])
            )
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/requests/{request_uuid}/status", response_model=RequestResponse)
async def update_request_status(request_uuid: str, status: RequestStatus):
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE requests SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE uuid = ?
            """, (status.value, request_uuid))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Request not found")
            
            conn.commit()
            
            return RequestResponse(
                uuid=request_uuid,
                status=status,
                message=f"Request status updated to {status.value}"
            )
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/requests/{request_uuid}/logs", response_model=WorkLogResponse)
async def get_work_logs(request_uuid: str, limit: int = 100, offset: int = 0):
    try:
        table_name = db.get_work_log_table_name(request_uuid)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Work log not found")
            
            cursor.execute(f"""
                SELECT * FROM {table_name} 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            total_count = cursor.fetchone()['count']
            
            logs = []
            for row in rows:
                logs.append(WorkLogEntry(
                    id=row['id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    output=row['output'],
                    log_type=row['log_type']
                ))
            
            return WorkLogResponse(
                request_uuid=request_uuid,
                logs=logs,
                total_entries=total_count
            )
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/requests/{request_uuid}", response_model=RequestResponse)
async def cancel_request(request_uuid: str):
    return await update_request_status(request_uuid, RequestStatus.CANCELLED)