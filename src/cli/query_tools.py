import click
import sqlite3
from datetime import datetime
from tabulate import tabulate
from typing import Optional

from ..database.connection import DatabaseConnection
from ..database.models import RequestStatus, LogType

db = DatabaseConnection()

@click.group()
def cli():
    """QEMU Simulation Query Tools"""
    pass

@cli.command()
@click.option('--status', type=click.Choice(['pending', 'acknowledged', 'running', 'cancelled', 'hold', 'done']), 
              help='Filter by request status')
@click.option('--limit', default=20, help='Number of requests to show')
def list_requests(status: Optional[str], limit: int):
    """List simulation requests"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT uuid, vm_name, status, created_at, updated_at, timeout
                    FROM requests 
                    WHERE status = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (status, limit))
            else:
                cursor.execute("""
                    SELECT uuid, vm_name, status, created_at, updated_at, timeout
                    FROM requests 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            
            if not rows:
                click.echo("No requests found.")
                return
            
            headers = ['UUID', 'VM Name', 'Status', 'Created', 'Updated', 'Timeout']
            table_data = []
            
            for row in rows:
                table_data.append([
                    row['uuid'][:8] + '...',
                    row['vm_name'],
                    row['status'],
                    row['created_at'][:19],
                    row['updated_at'][:19],
                    f"{row['timeout']}s"
                ])
            
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    except sqlite3.Error as e:
        click.echo(f"Database error: {e}", err=True)

@cli.command()
@click.argument('request_uuid')
def show_request(request_uuid: str):
    """Show detailed information about a specific request"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM requests WHERE uuid = ? OR uuid LIKE ?", 
                         (request_uuid, f"{request_uuid}%"))
            row = cursor.fetchone()
            
            if not row:
                click.echo(f"Request not found: {request_uuid}", err=True)
                return
            
            click.echo(f"Request Details:")
            click.echo(f"UUID: {row['uuid']}")
            click.echo(f"VM Name: {row['vm_name']}")
            click.echo(f"Commands: {row['commands']}")
            click.echo(f"Timeout: {row['timeout']}s")
            click.echo(f"Status: {row['status']}")
            click.echo(f"Created: {row['created_at']}")
            click.echo(f"Updated: {row['updated_at']}")
    
    except sqlite3.Error as e:
        click.echo(f"Database error: {e}", err=True)

@cli.command()
@click.argument('request_uuid')
@click.option('--limit', default=50, help='Number of log entries to show')
@click.option('--log-type', type=click.Choice(['boot', 'command', 'stdout', 'stderr']), 
              help='Filter by log type')
@click.option('--follow', '-f', is_flag=True, help='Follow log output (like tail -f)')
def show_logs(request_uuid: str, limit: int, log_type: Optional[str], follow: bool):
    """Show work logs for a specific request"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT uuid FROM requests WHERE uuid = ? OR uuid LIKE ?", 
                         (request_uuid, f"{request_uuid}%"))
            result = cursor.fetchone()
            
            if not result:
                click.echo(f"Request not found: {request_uuid}", err=True)
                return
            
            full_uuid = result['uuid']
            table_name = db.get_work_log_table_name(full_uuid)
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                click.echo(f"No work logs found for request {request_uuid}", err=True)
                return
            
            if follow:
                _follow_logs(cursor, table_name, log_type)
            else:
                _show_static_logs(cursor, table_name, limit, log_type)
    
    except sqlite3.Error as e:
        click.echo(f"Database error: {e}", err=True)

def _show_static_logs(cursor, table_name: str, limit: int, log_type: Optional[str]):
    """Show static log entries"""
    if log_type:
        cursor.execute(f"""
            SELECT timestamp, output, log_type FROM {table_name}
            WHERE log_type = ?
            ORDER BY id DESC LIMIT ?
        """, (log_type, limit))
    else:
        cursor.execute(f"""
            SELECT timestamp, output, log_type FROM {table_name}
            ORDER BY id DESC LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    
    if not rows:
        click.echo("No log entries found.")
        return
    
    for row in reversed(rows):
        timestamp = row['timestamp'][:19]
        log_type_colored = _colorize_log_type(row['log_type'])
        click.echo(f"[{timestamp}] {log_type_colored}: {row['output']}")

def _follow_logs(cursor, table_name: str, log_type: Optional[str]):
    """Follow log output in real-time"""
    click.echo("Following logs... (Press Ctrl+C to stop)")
    
    import time
    last_id = 0
    
    try:
        while True:
            if log_type:
                cursor.execute(f"""
                    SELECT id, timestamp, output, log_type FROM {table_name}
                    WHERE id > ? AND log_type = ?
                    ORDER BY id ASC
                """, (last_id, log_type))
            else:
                cursor.execute(f"""
                    SELECT id, timestamp, output, log_type FROM {table_name}
                    WHERE id > ?
                    ORDER BY id ASC
                """, (last_id,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                timestamp = row['timestamp'][:19]
                log_type_colored = _colorize_log_type(row['log_type'])
                click.echo(f"[{timestamp}] {log_type_colored}: {row['output']}")
                last_id = row['id']
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        click.echo("\nStopped following logs.")

def _colorize_log_type(log_type: str) -> str:
    """Add color to log type based on type"""
    colors = {
        'boot': 'cyan',
        'command': 'yellow',
        'stdout': 'green',
        'stderr': 'red'
    }
    color = colors.get(log_type, 'white')
    return click.style(log_type.upper(), fg=color)

@cli.command()
def stats():
    """Show system statistics"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT status, COUNT(*) as count FROM requests GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) as total FROM requests")
            total_requests = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT COUNT(*) as today FROM requests 
                WHERE DATE(created_at) = DATE('now')
            """)
            today_requests = cursor.fetchone()['today']
            
            cursor.execute("""
                SELECT vm_name, COUNT(*) as count FROM requests 
                GROUP BY vm_name ORDER BY count DESC LIMIT 5
            """)
            top_vms = cursor.fetchall()
            
            click.echo("System Statistics:")
            click.echo(f"Total Requests: {total_requests}")
            click.echo(f"Today's Requests: {today_requests}")
            click.echo()
            
            click.echo("Status Distribution:")
            for status in ['pending', 'acknowledged', 'running', 'cancelled', 'hold', 'done']:
                count = status_counts.get(status, 0)
                click.echo(f"  {status.capitalize()}: {count}")
            
            if top_vms:
                click.echo()
                click.echo("Top VM Names:")
                for vm in top_vms:
                    click.echo(f"  {vm['vm_name']}: {vm['count']} requests")
    
    except sqlite3.Error as e:
        click.echo(f"Database error: {e}", err=True)

@cli.command()
@click.argument('request_uuid')
@click.confirmation_option(prompt='Are you sure you want to delete this request and its logs?')
def delete_request(request_uuid: str):
    """Delete a request and its work logs"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT uuid FROM requests WHERE uuid = ? OR uuid LIKE ?", 
                         (request_uuid, f"{request_uuid}%"))
            result = cursor.fetchone()
            
            if not result:
                click.echo(f"Request not found: {request_uuid}", err=True)
                return
            
            full_uuid = result['uuid']
            table_name = db.get_work_log_table_name(full_uuid)
            
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute("DELETE FROM requests WHERE uuid = ?", (full_uuid,))
            
            conn.commit()
            click.echo(f"Deleted request {full_uuid} and its logs.")
    
    except sqlite3.Error as e:
        click.echo(f"Database error: {e}", err=True)

if __name__ == '__main__':
    cli()