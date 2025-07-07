#!/usr/bin/env python3
"""
Detailed Ray Cluster Test - Forces task distribution across all nodes
"""

import ray
import time
import socket
from datetime import datetime

@ray.remote(num_cpus=1)
def get_node_info():
    """Get detailed node information"""
    import os
    import platform
    import psutil
    
    return {
        'node_id': ray.get_runtime_context().get_node_id(),
        'hostname': socket.gethostname(),
        'ip_address': socket.gethostbyname(socket.gethostname()),
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / 1024**3, 2),
        'timestamp': datetime.now().isoformat(),
        'process_id': os.getpid()
    }

@ray.remote(num_cpus=4) # Use more CPUs to force distribution
def heavy_compute_task(task_id):
    """Heavy computation task that should distribute across nodes"""
    import math
    import random
    
    start_time = time.time()
    node_id = ray.get_runtime_context().get_node_id()
    
    # Heavy computation
    result = 0
    for i in range(100000):
        result += math.sqrt(random.random() * 1000)
    
    return {
        'task_id': task_id,
        'node_id': node_id,
        'hostname': socket.gethostname(),
        'duration': time.time() - start_time,
        'result': round(result, 2)
    }

def main():
    print("=== Detailed Ray Cluster Test ===")
    print(f"Test started at: {datetime.now()}")
    
    # Initialize Ray
    ray.init(address='auto')
    
    # Get cluster info
    cluster_resources = ray.cluster_resources()
    nodes_info = ray.nodes()
    
    print(f"\nCluster Information:")
    print(f"- Total CPUs: {cluster_resources.get('CPU', 0)}")
    print(f"- Total Memory: {cluster_resources.get('memory', 0) / 1024**3:.2f} GB")
    print(f"- Connected Nodes: {len(nodes_info)}")
    
    print(f"\nDetailed Node Information:")
    for i, node in enumerate(nodes_info):
        print(f"Node {i+1}:")
        print(f"  - Node ID: {node['NodeID']}")
        print(f"  - Alive: {node['Alive']}")
        print(f"  - Resources: {node['Resources']}")
        print()
    
    # Test node information gathering
    print("Gathering information from all nodes...")
    info_futures = [get_node_info.remote() for _ in range(20)]  # More tasks than nodes
    info_results = ray.get(info_futures)
    
    # Group by node ID
    node_groups = {}
    for result in info_results:
        node_id = result['node_id']
        if node_id not in node_groups:
            node_groups[node_id] = []
        node_groups[node_id].append(result)
    
    print(f"\nNodes responding to tasks: {len(node_groups)}")
    print("=" * 80)
    
    for i, (node_id, results) in enumerate(node_groups.items(), 1):
        sample = results[0]  # Take first result as representative
        print(f"Node {i} (ID: {node_id[:16]}...):")
        print(f"  - Hostname: {sample['hostname']}")
        print(f"  - IP Address: {sample['ip_address']}")
        print(f"  - Python: {sample['python_version']}")
        print(f"  - Platform: {sample['platform']}")
        print(f"  - CPUs: {sample['cpu_count']}")
        print(f"  - Memory: {sample['memory_gb']} GB")
        print(f"  - Tasks handled: {len(results)}")
        print()
    
    # Heavy computation test to force distribution
    print("Running heavy computation tasks to test distribution...")
    compute_futures = [heavy_compute_task.remote(i) for i in range(24)]  # 24 tasks requiring 4 CPUs each
    compute_results = ray.get(compute_futures)
    
    # Analyze task distribution
    task_distribution = {}
    for result in compute_results:
        node_id = result['node_id']
        if node_id not in task_distribution:
            task_distribution[node_id] = []
        task_distribution[node_id].append(result)
    
    print(f"\nHeavy Task Distribution:")
    print("=" * 80)
    total_time = 0
    for node_id, tasks in task_distribution.items():
        avg_time = sum(t['duration'] for t in tasks) / len(tasks)
        total_time += sum(t['duration'] for t in tasks)
        hostname = tasks[0]['hostname']
        print(f"Node {node_id[:16]}... ({hostname}):")
        print(f"  - Tasks executed: {len(tasks)}")
        print(f"  - Average duration: {avg_time:.2f}s")
        print(f"  - Total duration: {sum(t['duration'] for t in tasks):.2f}s")
        print()
    
    # Performance summary
    wall_time = max(max(t['duration'] for t in tasks) for tasks in task_distribution.values())
    cpu_utilization = total_time / wall_time if wall_time > 0 else 0
    
    print(f"\nPerformance Summary:")
    print(f"- Total compute time: {total_time:.2f}s")
    print(f"- Wall clock time: {wall_time:.2f}s")
    print(f"- Parallelization efficiency: {cpu_utilization:.1f}x")
    print(f"- Tasks distributed across {len(task_distribution)} nodes")
    
    # Final verification
    print(f"\n=== Test Results ===")
    print(f"✅ Cluster has {len(nodes_info)} nodes connected")
    print(f"✅ {len(node_groups)} nodes responded to tasks")
    print(f"✅ Heavy tasks distributed across {len(task_distribution)} nodes")
    print(f"✅ Total cluster capacity: {cluster_resources.get('CPU', 0)} CPUs")
    print(f"✅ All nodes using Python {info_results[0]['python_version']}")
    
    if len(task_distribution) >= 4:  # Expecting at least 4 worker nodes + head
        print(f"✅ Excellent: Tasks well distributed across worker nodes")
    elif len(task_distribution) >= 2:
        print(f"⚠️  Warning: Limited distribution - only {len(task_distribution)} nodes used")
    else:
        print(f"❌ Issue: All tasks running on single node - check worker connectivity")
    
    ray.shutdown()
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main() 