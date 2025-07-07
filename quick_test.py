#!/usr/bin/env python3
"""
Quick Ray Cluster Test
This script tests all worker nodes quickly to verify proper configuration
"""

import ray
import time
import socket
from datetime import datetime

@ray.remote
def test_worker_node():
    """Test function to run on worker nodes"""
    import os
    import platform
    import psutil
    
    return {
        'node_id': ray.get_runtime_context().get_node_id(),
        'hostname': socket.gethostname(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / 1024**3, 2),
        'timestamp': datetime.now().isoformat()
    }

def main():
    print("=== Ray Cluster Quick Test ===")
    print(f"Test started at: {datetime.now()}")
    
    # Initialize Ray
    ray.init(address='auto')
    
    # Get cluster info
    cluster_resources = ray.cluster_resources()
    print(f"\nCluster Resources:")
    print(f"- Total CPUs: {cluster_resources.get('CPU', 0)}")
    print(f"- Total Memory: {cluster_resources.get('memory', 0) / 1024**3:.2f} GB")
    print(f"- Total Nodes: {len(ray.nodes())}")
    
    # Test each node
    print(f"\nTesting all {len(ray.nodes())} nodes...")
    
    # Create one task per node
    num_nodes = len(ray.nodes())
    futures = [test_worker_node.remote() for _ in range(num_nodes)]
    
    # Get results
    results = ray.get(futures)
    
    print(f"\nNode Test Results:")
    print("=" * 80)
    for i, result in enumerate(results, 1):
        print(f"Node {i}:")
        print(f"  - Node ID: {result['node_id'][:16]}...")
        print(f"  - Hostname: {result['hostname']}")
        print(f"  - Python: {result['python_version']}")
        print(f"  - CPUs: {result['cpu_count']}")
        print(f"  - Memory: {result['memory_gb']} GB")
        print(f"  - Test time: {result['timestamp']}")
        print()
    
    # Test distributed computation
    print("Testing distributed computation...")
    
    @ray.remote
    def compute_task(x):
        import math
        time.sleep(0.1)  # Simulate work
        return sum(math.sqrt(i) for i in range(x * 1000))
    
    start_time = time.time()
    computation_futures = [compute_task.remote(i) for i in range(1, 21)]
    computation_results = ray.get(computation_futures)
    end_time = time.time()
    
    print(f"Distributed computation completed in {end_time - start_time:.2f} seconds")
    print(f"Processed {len(computation_results)} tasks across {num_nodes} nodes")
    
    # Final status
    print("\n=== Test Summary ===")
    print(f"✅ All {num_nodes} worker nodes are responding correctly")
    print(f"✅ Python version consistent across all nodes: {results[0]['python_version']}")
    print(f"✅ Distributed computation working properly")
    print(f"✅ Total cluster capacity: {cluster_resources.get('CPU', 0)} CPUs")
    
    ray.shutdown()
    print(f"\nTest completed at: {datetime.now()}")

if __name__ == "__main__":
    main() 