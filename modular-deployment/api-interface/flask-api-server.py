#!/usr/bin/env python3
"""
Flask REST API Server for Ray Cluster Management
Implements the OpenAPI specification for checkpoint-based deployment
"""

import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

# Add validation script to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'validation'))
from validate_checkpoint import CheckpointValidator

app = Flask(__name__)
CORS(app)

# Configuration
ANSIBLE_PLAYBOOK_DIR = os.path.join(os.path.dirname(__file__), '..', 'playbooks')
INVENTORY_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'inventory.ini')
CHECKPOINT_DIR = "/tmp"

# In-memory storage for execution tracking
executions = {}
executions_lock = threading.Lock()

class ExecutionTracker:
    def __init__(self, checkpoint, execution_id):
        self.checkpoint = checkpoint
        self.execution_id = execution_id
        self.status = "STARTED"
        self.started_at = datetime.now()
        self.process = None
        self.output = []
        self.error = None
        
    def to_dict(self):
        return {
            "checkpoint": self.checkpoint,
            "execution_id": self.execution_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "output": self.output,
            "error": self.error
        }

def get_checkpoint_validator():
    """Get configured checkpoint validator"""
    return CheckpointValidator(CHECKPOINT_DIR)

def run_ansible_playbook(checkpoint_name, execution_id):
    """Run ansible playbook in background thread"""
    playbook_file = f"{checkpoint_name.replace('_', '-')}.yml"
    playbook_path = os.path.join(ANSIBLE_PLAYBOOK_DIR, playbook_file)
    
    if not os.path.exists(playbook_path):
        with executions_lock:
            if execution_id in executions:
                executions[execution_id].status = "FAILED"
                executions[execution_id].error = f"Playbook not found: {playbook_path}"
        return
    
    try:
        with executions_lock:
            if execution_id in executions:
                executions[execution_id].status = "RUNNING"
        
        # Run ansible playbook
        cmd = [
            "ansible-playbook",
            "-i", INVENTORY_FILE,
            playbook_path
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        with executions_lock:
            if execution_id in executions:
                executions[execution_id].process = process
        
        # Stream output
        for line in process.stdout:
            with executions_lock:
                if execution_id in executions:
                    executions[execution_id].output.append(line.strip())
        
        process.wait()
        
        with executions_lock:
            if execution_id in executions:
                if process.returncode == 0:
                    executions[execution_id].status = "COMPLETED"
                else:
                    executions[execution_id].status = "FAILED"
                    executions[execution_id].error = f"Ansible playbook failed with return code {process.returncode}"
                    
    except Exception as e:
        with executions_lock:
            if execution_id in executions:
                executions[execution_id].status = "FAILED"
                executions[execution_id].error = str(e)

# API Routes

@app.route('/api/v1/cluster/status', methods=['GET'])
def get_cluster_status():
    """Get overall cluster status"""
    try:
        validator = get_checkpoint_validator()
        status = validator.get_cluster_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/cluster/health', methods=['GET'])
def get_cluster_health():
    """Get cluster health status"""
    try:
        validator = get_checkpoint_validator()
        status = validator.get_cluster_status()
        health = status.get('cluster_health', {})
        return jsonify(health)
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/checkpoints', methods=['GET'])
def list_checkpoints():
    """List all checkpoints"""
    try:
        validator = get_checkpoint_validator()
        status = validator.get_cluster_status()
        checkpoints = []
        
        for checkpoint_name in validator.CHECKPOINT_ORDER:
            checkpoint_data = status['checkpoint_details'].get(checkpoint_name, {})
            checkpoints.append(checkpoint_data)
        
        return jsonify(checkpoints)
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/checkpoints/<checkpoint_name>', methods=['GET'])
def get_checkpoint_status(checkpoint_name):
    """Get specific checkpoint status"""
    try:
        validator = get_checkpoint_validator()
        result = validator.validate_checkpoint(checkpoint_name)
        
        if result['status'] == 'NOT_FOUND':
            return jsonify({"error": "Checkpoint not found", "checkpoint": checkpoint_name}), 404
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/checkpoints/<checkpoint_name>', methods=['POST'])
def execute_checkpoint(checkpoint_name):
    """Execute a specific checkpoint"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)
        approve = data.get('approve', False)
        
        # Check if checkpoint requires approval
        validator = get_checkpoint_validator()
        approval_info = validator.check_approval_required(checkpoint_name)
        
        if approval_info['approval_required'] and not approve:
            # Check if approval file exists
            approval_file = approval_info['approval_file']
            if not os.path.exists(approval_file):
                return jsonify({
                    "error": "APPROVAL_REQUIRED",
                    "checkpoint": checkpoint_name,
                    "approval_info": approval_info,
                    "message": f"Checkpoint {checkpoint_name} requires human approval"
                }), 400
        
        # Create approval file if approve=true
        if approve and approval_info['approval_required']:
            approval_file = approval_info['approval_file']
            with open(approval_file, 'w') as f:
                f.write(json.dumps({
                    "approved_at": datetime.now().isoformat(),
                    "approved_by": "API",
                    "checkpoint": checkpoint_name
                }))
        
        # Start execution
        execution_id = str(uuid.uuid4())
        tracker = ExecutionTracker(checkpoint_name, execution_id)
        
        with executions_lock:
            executions[execution_id] = tracker
        
        # Start background thread
        thread = threading.Thread(
            target=run_ansible_playbook,
            args=(checkpoint_name, execution_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "checkpoint": checkpoint_name,
            "execution_id": execution_id,
            "status": "STARTED",
            "started_at": tracker.started_at.isoformat(),
            "message": f"Checkpoint {checkpoint_name} execution started"
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/executions/<execution_id>', methods=['GET'])
def get_execution_status(execution_id):
    """Get execution status"""
    with executions_lock:
        if execution_id not in executions:
            return jsonify({"error": "Execution not found"}), 404
        
        execution = executions[execution_id]
        return jsonify(execution.to_dict())

@app.route('/api/v1/approvals/<checkpoint_name>', methods=['GET'])
def get_approval_requirements(checkpoint_name):
    """Get approval requirements for checkpoint"""
    try:
        validator = get_checkpoint_validator()
        approval_info = validator.check_approval_required(checkpoint_name)
        
        # Add impact summary
        impact_summary = []
        if checkpoint_name == "docker-installation":
            impact_summary = [
                "Install Docker packages on all nodes",
                "Modify system configuration",
                "Add users to docker group",
                "Start Docker service"
            ]
        elif checkpoint_name == "cleanup-existing":
            impact_summary = [
                "⚠️ DESTRUCTIVE: Remove all existing Ray containers",
                "⚠️ DESTRUCTIVE: Kill Ray processes",
                "⚠️ DESTRUCTIVE: Delete Ray temporary directories",
                "⚠️ DESTRUCTIVE: Remove Ray configuration files"
            ]
        
        approval_info['impact_summary'] = impact_summary
        return jsonify(approval_info)
        
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/approvals/<checkpoint_name>', methods=['POST'])
def grant_approval(checkpoint_name):
    """Grant approval for checkpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        approved_by = data.get('approved_by')
        reason = data.get('reason')
        acknowledge_risks = data.get('acknowledge_risks', False)
        
        if not approved_by or not reason:
            return jsonify({"error": "approved_by and reason are required"}), 400
        
        # Get approval requirements
        validator = get_checkpoint_validator()
        approval_info = validator.check_approval_required(checkpoint_name)
        
        if not approval_info['approval_required']:
            return jsonify({"error": "Checkpoint does not require approval"}), 400
        
        if approval_info['destructive_operation'] and not acknowledge_risks:
            return jsonify({"error": "Must acknowledge risks for destructive operations"}), 400
        
        # Create approval file
        approval_file = approval_info['approval_file']
        approval_data = {
            "checkpoint": checkpoint_name,
            "approved_by": approved_by,
            "reason": reason,
            "approved_at": datetime.now().isoformat(),
            "acknowledge_risks": acknowledge_risks,
            "destructive_operation": approval_info['destructive_operation']
        }
        
        with open(approval_file, 'w') as f:
            json.dump(approval_data, f, indent=2)
        
        return jsonify({
            "checkpoint": checkpoint_name,
            "approved": True,
            "approved_by": approved_by,
            "approved_at": approval_data['approved_at'],
            "approval_token": f"approval_{checkpoint_name}_{int(time.time())}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/nodes', methods=['GET'])
def list_nodes():
    """List cluster nodes"""
    try:
        # Parse inventory file
        nodes = []
        inventory_path = INVENTORY_FILE
        
        if os.path.exists(inventory_path):
            with open(inventory_path, 'r') as f:
                content = f.read()
                
            # Simple inventory parsing
            current_group = None
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_group = line[1:-1]
                elif line and not line.startswith('#') and '=' in line:
                    parts = line.split()
                    node_name = parts[0]
                    
                    # Extract ansible_host
                    ip = None
                    for part in parts[1:]:
                        if part.startswith('ansible_host='):
                            ip = part.split('=')[1]
                            break
                    
                    role = "head" if "head" in current_group else "worker"
                    
                    nodes.append({
                        "name": node_name,
                        "ip": ip,
                        "role": role,
                        "status": "UNKNOWN",  # Would need to check actual connectivity
                        "containers": []  # Would need to query Docker
                    })
        
        return jsonify(nodes)
        
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    print("Starting Ray Cluster Management API Server...")
    print(f"Ansible Playbooks: {ANSIBLE_PLAYBOOK_DIR}")
    print(f"Inventory File: {INVENTORY_FILE}")
    print(f"Checkpoint Data: {CHECKPOINT_DIR}")
    
    app.run(host='0.0.0.0', port=8000, debug=True) 