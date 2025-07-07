#!/usr/bin/env python3
"""
Ray Cluster Master Deployment Orchestrator
Manages checkpoint-based deployment with human-in-the-loop approval
"""

import os
import sys
import json
import subprocess
import argparse
import time
from datetime import datetime

class DeploymentOrchestrator:
    """Orchestrates the complete Ray cluster deployment process"""
    
    CHECKPOINTS = [
        {
            "name": "prerequisites-check",
            "description": "Validate system requirements and connectivity",
            "approval_required": False,
            "destructive": False
        },
        {
            "name": "docker-installation",
            "description": "Install and configure Docker on all nodes",
            "approval_required": True,
            "destructive": False
        },
        {
            "name": "cleanup-existing",
            "description": "Remove existing Ray installations",
            "approval_required": True,
            "destructive": True
        },
        {
            "name": "ray-deployment",
            "description": "Deploy Ray head and worker nodes",
            "approval_required": False,
            "destructive": False
        },
        {
            "name": "monitoring-deployment",
            "description": "Deploy monitoring stack (Prometheus, Grafana)",
            "approval_required": False,
            "destructive": False
        },
        {
            "name": "final-validation",
            "description": "Comprehensive cluster validation and testing",
            "approval_required": False,
            "destructive": False
        }
    ]
    
    def __init__(self, playbook_dir="modular-deployment/playbooks"):
        self.playbook_dir = playbook_dir
        self.inventory_file = "inventory.ini"
        
    def run_checkpoint(self, checkpoint_name, auto_approve=False):
        """Run a specific checkpoint"""
        checkpoint = next((c for c in self.CHECKPOINTS if c["name"] == checkpoint_name), None)
        if not checkpoint:
            raise ValueError(f"Unknown checkpoint: {checkpoint_name}")
        
        print(f"\n{'='*60}")
        print(f"CHECKPOINT: {checkpoint['name'].upper()}")
        print(f"Description: {checkpoint['description']}")
        print(f"Approval Required: {checkpoint['approval_required']}")
        print(f"Destructive Operation: {checkpoint['destructive']}")
        print(f"{'='*60}")
        
        # Check if approval is required
        if checkpoint['approval_required'] and not auto_approve:
            self._request_approval(checkpoint)
        
        # Run the playbook
        playbook_file = f"{checkpoint_name.replace('_', '-')}.yml"
        playbook_path = os.path.join(self.playbook_dir, playbook_file)
        
        if not os.path.exists(playbook_path):
            raise FileNotFoundError(f"Playbook not found: {playbook_path}")
        
        print(f"\nExecuting playbook: {playbook_path}")
        cmd = [
            "ansible-playbook",
            "-i", self.inventory_file,
            playbook_path
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            raise RuntimeError(f"Checkpoint {checkpoint_name} failed with return code {result.returncode}")
        
        print(f"✅ Checkpoint {checkpoint_name} completed successfully")
        return True
    
    def _request_approval(self, checkpoint):
        """Request human approval for checkpoint"""
        print(f"\n⚠️  APPROVAL REQUIRED ⚠️")
        print(f"Checkpoint: {checkpoint['name']}")
        print(f"Description: {checkpoint['description']}")
        
        if checkpoint['destructive']:
            print("🔥 WARNING: This is a DESTRUCTIVE operation!")
            print("This action cannot be undone.")
        
        print(f"\nWhat this checkpoint will do:")
        
        # Specific warnings for each checkpoint
        if checkpoint['name'] == 'docker-installation':
            print("• Install Docker packages on all cluster nodes")
            print("• Modify system configuration")
            print("• Add users to docker group")
            print("• Start Docker service")
            
        elif checkpoint['name'] == 'cleanup-existing':
            print("• Stop and remove all existing Ray containers")
            print("• Kill any running Ray processes")
            print("• Delete Ray temporary directories")
            print("• Remove Ray configuration files")
            print("• THIS WILL DESTROY ANY EXISTING RAY CLUSTER!")
        
        while True:
            response = input(f"\nDo you approve execution of '{checkpoint['name']}'? (yes/no): ").lower().strip()
            
            if response in ['yes', 'y']:
                # Create approval file
                approval_file = f"/tmp/checkpoint-{checkpoint['name']}-approved"
                approval_data = {
                    "checkpoint": checkpoint['name'],
                    "approved_by": "interactive_user",
                    "approved_at": datetime.now().isoformat(),
                    "method": "interactive"
                }
                
                with open(approval_file, 'w') as f:
                    json.dump(approval_data, f, indent=2)
                
                print(f"✅ Approval granted for {checkpoint['name']}")
                break
                
            elif response in ['no', 'n']:
                print(f"❌ Approval denied for {checkpoint['name']}")
                print("Deployment aborted.")
                sys.exit(1)
                
            else:
                print("Please enter 'yes' or 'no'")
    
    def validate_prerequisites(self):
        """Validate that prerequisites are met before starting"""
        print("Validating deployment prerequisites...")
        
        # Check inventory file exists
        if not os.path.exists(self.inventory_file):
            raise FileNotFoundError(f"Inventory file not found: {self.inventory_file}")
        
        # Check playbook directory exists
        if not os.path.exists(self.playbook_dir):
            raise FileNotFoundError(f"Playbook directory not found: {self.playbook_dir}")
        
        # Check all required playbooks exist
        missing_playbooks = []
        for checkpoint in self.CHECKPOINTS:
            playbook_file = f"{checkpoint['name'].replace('_', '-')}.yml"
            playbook_path = os.path.join(self.playbook_dir, playbook_file)
            if not os.path.exists(playbook_path):
                missing_playbooks.append(playbook_path)
        
        if missing_playbooks:
            raise FileNotFoundError(f"Missing playbooks: {missing_playbooks}")
        
        # Test Ansible connectivity
        print("Testing Ansible connectivity...")
        cmd = ["ansible", "all", "-i", self.inventory_file, "-m", "ping"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Warning: Ansible connectivity test failed")
            print(result.stderr)
            response = input("Continue anyway? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                sys.exit(1)
        
        print("✅ Prerequisites validated")
    
    def deploy_full_cluster(self, start_from=None, auto_approve=False):
        """Deploy the complete Ray cluster"""
        print("🚀 Starting Ray Cluster Deployment")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Auto-approve: {auto_approve}")
        
        # Validate prerequisites
        self.validate_prerequisites()
        
        # Find starting checkpoint
        start_index = 0
        if start_from:
            try:
                start_index = next(i for i, c in enumerate(self.CHECKPOINTS) if c["name"] == start_from)
                print(f"Starting from checkpoint: {start_from}")
            except StopIteration:
                raise ValueError(f"Unknown checkpoint: {start_from}")
        
        # Execute checkpoints
        for i, checkpoint in enumerate(self.CHECKPOINTS[start_index:], start_index):
            try:
                print(f"\n📍 Checkpoint {i+1}/{len(self.CHECKPOINTS)}")
                self.run_checkpoint(checkpoint["name"], auto_approve)
                
                # Wait a moment between checkpoints
                if i < len(self.CHECKPOINTS) - 1:
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Deployment failed at checkpoint: {checkpoint['name']}")
                print(f"Error: {e}")
                
                # Save failure state
                failure_info = {
                    "failed_checkpoint": checkpoint["name"],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "completed_checkpoints": [c["name"] for c in self.CHECKPOINTS[:i]]
                }
                
                with open("/tmp/deployment-failure.json", "w") as f:
                    json.dump(failure_info, f, indent=2)
                
                print(f"Failure information saved to: /tmp/deployment-failure.json")
                print(f"To resume, use: --start-from {checkpoint['name']}")
                sys.exit(1)
        
        # Success!
        print("\n🎉 RAY CLUSTER DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print(f"Deployment completed at: {datetime.now().isoformat()}")
        
        # Save completion marker
        completion_info = {
            "status": "COMPLETED",
            "completed_at": datetime.now().isoformat(),
            "checkpoints_completed": [c["name"] for c in self.CHECKPOINTS],
            "auto_approved": auto_approve
        }
        
        with open("/tmp/deployment-complete.json", "w") as f:
            json.dump(completion_info, f, indent=2)
        
        print("\n📊 Access your Ray cluster:")
        print("• Ray Dashboard: http://<head-node-ip>:8265")
        print("• Prometheus: http://<head-node-ip>:9090")
        print("• Grafana: http://<head-node-ip>:3000 (admin/admin123)")
    
    def list_checkpoints(self):
        """List all available checkpoints"""
        print("Available Checkpoints:")
        print("-" * 60)
        
        for i, checkpoint in enumerate(self.CHECKPOINTS, 1):
            approval_icon = "🔒" if checkpoint['approval_required'] else "🔓"
            destructive_icon = "💥" if checkpoint['destructive'] else "✨"
            
            print(f"{i}. {checkpoint['name']}")
            print(f"   {approval_icon} Approval: {'Required' if checkpoint['approval_required'] else 'Not Required'}")
            print(f"   {destructive_icon} Destructive: {'Yes' if checkpoint['destructive'] else 'No'}")
            print(f"   Description: {checkpoint['description']}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Ray Cluster Deployment Orchestrator')
    parser.add_argument('--list-checkpoints', action='store_true', help='List all available checkpoints')
    parser.add_argument('--checkpoint', '-c', help='Run a specific checkpoint')
    parser.add_argument('--deploy', action='store_true', help='Deploy the complete cluster')
    parser.add_argument('--start-from', help='Start deployment from specific checkpoint')
    parser.add_argument('--auto-approve', action='store_true', help='Automatically approve all checkpoints (DANGEROUS)')
    parser.add_argument('--playbook-dir', default='modular-deployment/playbooks', help='Path to playbook directory')
    
    args = parser.parse_args()
    
    orchestrator = DeploymentOrchestrator(args.playbook_dir)
    
    try:
        if args.list_checkpoints:
            orchestrator.list_checkpoints()
        
        elif args.checkpoint:
            orchestrator.run_checkpoint(args.checkpoint, args.auto_approve)
        
        elif args.deploy:
            if args.auto_approve:
                print("⚠️  WARNING: Auto-approve mode enabled. This will bypass all safety checks!")
                response = input("Are you sure? (yes/no): ").lower().strip()
                if response not in ['yes', 'y']:
                    print("Deployment aborted.")
                    sys.exit(1)
            
            orchestrator.deploy_full_cluster(args.start_from, args.auto_approve)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 