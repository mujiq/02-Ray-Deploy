#!/usr/bin/env python3
"""
Ray Cluster Checkpoint Validation Script
Validates checkpoint results and provides status reporting for REST API integration
"""

import json
import sys
import os
import glob
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any

class CheckpointValidator:
    """Validates and reports on Ray cluster deployment checkpoints"""
    
    CHECKPOINT_ORDER = [
        "prerequisites-check",
        "docker-installation", 
        "cleanup-existing",
        "ray-deployment",
        "monitoring-deployment",
        "final-validation"
    ]
    
    def __init__(self, checkpoint_dir: str = "/tmp"):
        self.checkpoint_dir = checkpoint_dir
        self.results = {}
        
    def load_checkpoint_results(self, checkpoint_name: Optional[str] = None) -> Dict[str, Any]:
        """Load checkpoint results from JSON files"""
        pattern = f"checkpoint-{checkpoint_name}-*.json" if checkpoint_name else "checkpoint-*.json"
        files = glob.glob(os.path.join(self.checkpoint_dir, pattern))
        
        results = {}
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    checkpoint = data.get('checkpoint')
                    node = data.get('node')
                    
                    if checkpoint not in results:
                        results[checkpoint] = {}
                    results[checkpoint][node] = data
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
        return results
    
    def validate_checkpoint(self, checkpoint_name: str) -> Dict[str, Any]:
        """Validate a specific checkpoint"""
        results = self.load_checkpoint_results(checkpoint_name)
        
        if checkpoint_name not in results:
            return {
                "checkpoint": checkpoint_name,
                "status": "NOT_FOUND",
                "message": f"No results found for checkpoint {checkpoint_name}",
                "nodes": {},
                "total_nodes": 0,
                "passed_nodes": 0
            }
        
        checkpoint_data = results[checkpoint_name]
        all_passed = True
        node_status = {}
        
        for node, data in checkpoint_data.items():
            status = data.get('status', 'UNKNOWN')
            node_status[node] = {
                "status": status,
                "timestamp": data.get('timestamp'),
                "approval_required": data.get('approval_required', False),
                "destructive_operation": data.get('destructive_operation', False)
            }
            
            if status != "PASSED":
                all_passed = False
        
        return {
            "checkpoint": checkpoint_name,
            "status": "PASSED" if all_passed else "FAILED",
            "nodes": node_status,
            "total_nodes": len(node_status),
            "passed_nodes": sum(1 for n in node_status.values() if n["status"] == "PASSED")
        }
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get overall cluster deployment status"""
        all_results = self.load_checkpoint_results()
        
        checkpoint_status = {}
        for checkpoint in self.CHECKPOINT_ORDER:
            checkpoint_status[checkpoint] = self.validate_checkpoint(checkpoint)
        
        # Determine overall status
        completed_checkpoints = [
            name for name, data in checkpoint_status.items() 
            if data["status"] == "PASSED"
        ]
        
        # Check if deployment is complete
        deployment_complete = len(completed_checkpoints) == len(self.CHECKPOINT_ORDER)
        
        # Get cluster health from final validation if available
        cluster_health = self._extract_cluster_health(all_results)
        
        return {
            "deployment_status": "COMPLETED" if deployment_complete else "IN_PROGRESS",
            "completed_checkpoints": completed_checkpoints,
            "total_checkpoints": len(self.CHECKPOINT_ORDER),
            "checkpoint_details": checkpoint_status,
            "cluster_health": cluster_health,
            "last_updated": datetime.now().isoformat()
        }
    
    def _extract_cluster_health(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract cluster health information from validation results"""
        if "final-validation" not in all_results:
            return {"status": "UNKNOWN", "message": "No validation data available"}
        
        validation_data = all_results["final-validation"]
        health = {
            "ray_cluster": {"status": "UNKNOWN", "nodes": 0},
            "monitoring": {"status": "UNKNOWN", "services": []},
            "containers": {"total": 0, "running": 0},
            "endpoints": {"healthy": 0, "total": 0}
        }
        
        for node, data in validation_data.items():
            # Container information
            container_count = data.get("containers_running", 0)
            health["containers"]["total"] += container_count
            health["containers"]["running"] += container_count
            
            # Ray cluster status
            if data.get("node_type") == "head" and data.get("ray_cluster_status"):
                ray_status = data.get("ray_cluster_status", [])
                for line in ray_status:
                    if "Active:" in line:
                        # Parse active nodes
                        parts = line.split("Active:")[1].strip()
                        if parts and not parts.startswith("(no"):
                            health["ray_cluster"]["nodes"] = len([l for l in ray_status if "node_" in l])
                            health["ray_cluster"]["status"] = "HEALTHY"
            
            # Monitoring endpoints
            endpoints = data.get("monitoring_endpoints", [])
            for endpoint in endpoints:
                health["endpoints"]["total"] += 1
                if endpoint.get("status") == 200:
                    health["endpoints"]["healthy"] += 1
        
        # Overall health determination
        if health["ray_cluster"]["status"] == "HEALTHY" and health["endpoints"]["healthy"] > 0:
            health["overall_status"] = "HEALTHY"
        else:
            health["overall_status"] = "DEGRADED"
        
        return health
    
    def generate_report(self, format_type: str = "json") -> str:
        """Generate a status report in specified format"""
        status = self.get_cluster_status()
        
        if format_type == "json":
            return json.dumps(status, indent=2)
        
        elif format_type == "text":
            report = []
            report.append("=" * 50)
            report.append("RAY CLUSTER DEPLOYMENT STATUS")
            report.append("=" * 50)
            report.append(f"Overall Status: {status['deployment_status']}")
            report.append(f"Completed Checkpoints: {len(status['completed_checkpoints'])}/{status['total_checkpoints']}")
            report.append("")
            
            report.append("CHECKPOINT STATUS:")
            for checkpoint, details in status['checkpoint_details'].items():
                status_icon = "✅" if details['status'] == "PASSED" else "❌"
                report.append(f"{status_icon} {checkpoint}: {details['status']} ({details['passed_nodes']}/{details['total_nodes']} nodes)")
            
            if status.get('cluster_health'):
                health = status['cluster_health']
                report.append("")
                report.append("CLUSTER HEALTH:")
                report.append(f"Overall: {health.get('overall_status', 'UNKNOWN')}")
                report.append(f"Ray Nodes: {health.get('ray_cluster', {}).get('nodes', 0)}")
                report.append(f"Containers: {health.get('containers', {}).get('running', 0)}")
                report.append(f"Monitoring: {health.get('endpoints', {}).get('healthy', 0)}/{health.get('endpoints', {}).get('total', 0)} endpoints")
            
            return "\n".join(report)
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def check_approval_required(self, checkpoint_name: str) -> Dict[str, Any]:
        """Check if a checkpoint requires approval"""
        results = self.load_checkpoint_results(checkpoint_name)
        
        if checkpoint_name not in results:
            return {"approval_required": False, "message": "Checkpoint not found"}
        
        # Check any node's approval requirement (should be consistent)
        sample_node = next(iter(results[checkpoint_name].values()))
        approval_required = sample_node.get('approval_required', False)
        destructive = sample_node.get('destructive_operation', False)
        
        return {
            "checkpoint": checkpoint_name,
            "approval_required": approval_required,
            "destructive_operation": destructive,
            "approval_file": f"/tmp/checkpoint-{checkpoint_name}-approved",
            "message": f"Approval {'required' if approval_required else 'not required'} for {checkpoint_name}"
        }

def main():
    parser = argparse.ArgumentParser(description='Validate Ray cluster checkpoint status')
    parser.add_argument('--checkpoint', '-c', help='Specific checkpoint to validate')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json', help='Output format')
    parser.add_argument('--approval-check', '-a', help='Check approval requirements for checkpoint')
    parser.add_argument('--health-only', action='store_true', help='Show only cluster health status')
    
    args = parser.parse_args()
    
    validator = CheckpointValidator()
    
    try:
        if args.approval_check:
            result = validator.check_approval_required(args.approval_check)
            print(json.dumps(result, indent=2))
        
        elif args.health_only:
            status = validator.get_cluster_status()
            health = status.get('cluster_health', {})
            print(json.dumps(health, indent=2))
        
        elif args.checkpoint:
            result = validator.validate_checkpoint(args.checkpoint)
            print(json.dumps(result, indent=2) if args.format == 'json' else result)
        
        else:
            report = validator.generate_report(args.format)
            print(report)
    
    except Exception as e:
        error = {"error": str(e), "timestamp": datetime.now().isoformat()}
        print(json.dumps(error, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main() 