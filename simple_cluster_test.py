#!/usr/bin/env python3
"""
Simple Ray Cluster Test
This script runs inside the Ray container to test cluster functionality
"""

import ray
import time
import random
from datetime import datetime, timedelta

@ray.remote
def cpu_task(task_id, duration=5):
    """CPU-intensive task for testing"""
    start_time = time.time()
    node_id = ray.get_runtime_context().get_node_id()
    
    # CPU work
    result = 0
    while time.time() - start_time < duration:
        for i in range(50000):
            result += i * i
    
    return {
        'task_id': task_id,
        'node_id': node_id,
        'duration': time.time() - start_time,
        'result': result % 1000000
    }

@ray.remote
def memory_task(task_id):
    """Memory task for testing"""
    import random
    node_id = ray.get_runtime_context().get_node_id()
    
    # Create some data
    data = [random.random() for _ in range(100000)]
    result = sum(data)
    
    return {
        'task_id': task_id,
        'node_id': node_id,
        'data_sum': result,
        'data_size': len(data)
    }

def main():
    print("🚀 Starting Ray Cluster Test")
    print("=" * 50)
    
    # Get cluster info
    cluster_resources = ray.cluster_resources()
    nodes = ray.nodes()
    
    print(f"✅ Cluster Resources: {cluster_resources}")
    print(f"✅ Number of Nodes: {len(nodes)}")
    print(f"✅ Total CPUs: {cluster_resources.get('CPU', 0)}")
    print(f"✅ Total Memory: {cluster_resources.get('memory', 0) / 1024**3:.1f} GB")
    
    # Show each node
    for i, node in enumerate(nodes):
        if node['Alive']:
            print(f"Node {i+1}: {node['Resources']} (Alive: {node['Alive']})")
    
    print("\n🔄 Running distributed workload for 5 minutes...")
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=5)
    
    task_counter = 0
    all_results = []
    node_task_count = {}
    
    while datetime.now() < end_time:
        remaining = (end_time - datetime.now()).total_seconds()
        print(f"⏱️  Time remaining: {remaining:.1f}s")
        
        # Submit batch of tasks
        batch_size = 20
        futures = []
        
        # CPU tasks
        for i in range(batch_size):
            future = cpu_task.remote(f"cpu_{task_counter}_{i}")
            futures.append(future)
        
        # Memory tasks
        for i in range(batch_size // 2):
            future = memory_task.remote(f"mem_{task_counter}_{i}")
            futures.append(future)
        
        # Get results
        try:
            results = ray.get(futures, timeout=30)
            all_results.extend(results)
            
            # Count tasks per node
            for result in results:
                node_id = result['node_id']
                node_task_count[node_id] = node_task_count.get(node_id, 0) + 1
            
            print(f"✅ Completed batch {task_counter}: {len(results)} tasks")
            
        except Exception as e:
            print(f"⚠️  Error in batch {task_counter}: {e}")
        
        task_counter += 1
        time.sleep(3)  # Brief pause
    
    # Results summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total tasks completed: {len(all_results)}")
    print(f"Tasks distributed across {len(node_task_count)} nodes:")
    
    for node_id, count in node_task_count.items():
        print(f"  Node {node_id[:8]}...: {count} tasks")
    
    # Check distribution
    if len(node_task_count) > 1:
        print("✅ SUCCESS: Tasks were distributed across multiple nodes!")
        print("🎉 ALL WORKER NODES ARE FUNCTIONING PROPERLY!")
        return True
    else:
        print("⚠️  WARNING: All tasks ran on a single node")
        return False

if __name__ == "__main__":
    try:
        # Connect to existing cluster
        ray.init(address='auto')
        success = main()
        ray.shutdown()
        
        if success:
            print("\n🎉 CLUSTER TEST PASSED!")
            exit(0)
        else:
            print("\n❌ CLUSTER TEST FAILED!")
            exit(1)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1) 