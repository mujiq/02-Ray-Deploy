#!/usr/bin/env python3
"""
Ray Cluster Health Test Script
This script tests the Ray cluster by running distributed tasks across all nodes
for 5 minutes to verify proper functionality and worker node configuration.
"""

import ray
import time
import numpy as np
import psutil
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@ray.remote
def cpu_intensive_task(task_id, duration=10):
    """CPU-intensive task to test worker node performance"""
    start_time = time.time()
    node_id = ray.get_runtime_context().get_node_id()
    
    # Simulate CPU-intensive work
    result = 0
    while time.time() - start_time < duration:
        for i in range(100000):
            result += i * i
    
    end_time = time.time()
    return {
        'task_id': task_id,
        'node_id': node_id,
        'duration': end_time - start_time,
        'result': result,
        'worker_pid': ray.get_runtime_context().get_worker_id()
    }

@ray.remote
def memory_intensive_task(task_id, array_size=10000000):
    """Memory-intensive task to test worker node memory handling"""
    start_time = time.time()
    node_id = ray.get_runtime_context().get_node_id()
    
    # Create large numpy arrays
    arrays = []
    for i in range(5):
        arr = np.random.random(array_size)
        arrays.append(arr.sum())
    
    end_time = time.time()
    return {
        'task_id': task_id,
        'node_id': node_id,
        'duration': end_time - start_time,
        'array_sums': arrays,
        'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
    }

@ray.remote
def communication_test(task_id, message_size=1000):
    """Test inter-node communication"""
    start_time = time.time()
    node_id = ray.get_runtime_context().get_node_id()
    
    # Create data to pass around
    data = np.random.random(message_size).tolist()
    processed_data = [x * 2 for x in data]
    
    end_time = time.time()
    return {
        'task_id': task_id,
        'node_id': node_id,
        'duration': end_time - start_time,
        'data_checksum': sum(processed_data),
        'message_size': len(processed_data)
    }

def get_cluster_info():
    """Get detailed cluster information"""
    try:
        cluster_resources = ray.cluster_resources()
        nodes = ray.nodes()
        
        logger.info("=== CLUSTER INFORMATION ===")
        logger.info(f"Total Cluster Resources: {cluster_resources}")
        logger.info(f"Number of Nodes: {len(nodes)}")
        
        for i, node in enumerate(nodes):
            logger.info(f"Node {i+1}:")
            logger.info(f"  Node ID: {node['NodeID']}")
            logger.info(f"  Alive: {node['Alive']}")
            logger.info(f"  Resources: {node['Resources']}")
            logger.info(f"  IP: {node.get('NodeManagerAddress', 'N/A')}")
        
        return cluster_resources, nodes
    except Exception as e:
        logger.error(f"Error getting cluster info: {e}")
        return None, None

def run_distributed_workload():
    """Run distributed workload across all worker nodes"""
    logger.info("=== STARTING DISTRIBUTED WORKLOAD ===")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=5)
    
    task_counter = 0
    all_results = {
        'cpu_tasks': [],
        'memory_tasks': [],
        'communication_tasks': []
    }
    
    while datetime.now() < end_time:
        current_time = datetime.now()
        remaining_time = (end_time - current_time).total_seconds()
        
        logger.info(f"Time remaining: {remaining_time:.1f} seconds")
        
        # Submit batch of tasks
        batch_size = 10
        
        # CPU-intensive tasks
        cpu_futures = []
        for i in range(batch_size):
            future = cpu_intensive_task.remote(f"cpu_{task_counter}_{i}", duration=5)
            cpu_futures.append(future)
        
        # Memory-intensive tasks
        memory_futures = []
        for i in range(batch_size // 2):
            future = memory_intensive_task.remote(f"memory_{task_counter}_{i}")
            memory_futures.append(future)
        
        # Communication tasks
        comm_futures = []
        for i in range(batch_size):
            future = communication_test.remote(f"comm_{task_counter}_{i}")
            comm_futures.append(future)
        
        # Wait for tasks to complete
        try:
            cpu_results = ray.get(cpu_futures, timeout=30)
            memory_results = ray.get(memory_futures, timeout=30)
            comm_results = ray.get(comm_futures, timeout=30)
            
            all_results['cpu_tasks'].extend(cpu_results)
            all_results['memory_tasks'].extend(memory_results)
            all_results['communication_tasks'].extend(comm_results)
            
            logger.info(f"Completed batch {task_counter}: {len(cpu_results)} CPU, {len(memory_results)} memory, {len(comm_results)} comm tasks")
            
        except ray.exceptions.GetTimeoutError:
            logger.warning(f"Some tasks in batch {task_counter} timed out")
        except Exception as e:
            logger.error(f"Error in batch {task_counter}: {e}")
        
        task_counter += 1
        time.sleep(2)  # Brief pause between batches
    
    return all_results

def analyze_results(results):
    """Analyze test results and generate report"""
    logger.info("=== ANALYZING RESULTS ===")
    
    # Analyze node distribution
    node_distribution = {}
    
    for task_type, tasks in results.items():
        logger.info(f"\n{task_type.upper()} Results:")
        logger.info(f"  Total tasks completed: {len(tasks)}")
        
        if tasks:
            # Calculate average duration
            avg_duration = sum(task['duration'] for task in tasks) / len(tasks)
            logger.info(f"  Average duration: {avg_duration:.2f} seconds")
            
            # Count tasks per node
            task_nodes = {}
            for task in tasks:
                node_id = task['node_id']
                if node_id not in task_nodes:
                    task_nodes[node_id] = 0
                task_nodes[node_id] += 1
            
            logger.info(f"  Tasks per node: {task_nodes}")
            
            # Update overall node distribution
            for node_id, count in task_nodes.items():
                if node_id not in node_distribution:
                    node_distribution[node_id] = 0
                node_distribution[node_id] += count
    
    logger.info(f"\nOverall task distribution across nodes: {node_distribution}")
    
    # Check if tasks were distributed across multiple nodes
    unique_nodes = len(node_distribution)
    logger.info(f"Tasks executed on {unique_nodes} different nodes")
    
    if unique_nodes > 1:
        logger.info("✅ SUCCESS: Tasks were distributed across multiple worker nodes")
    else:
        logger.warning("⚠️  WARNING: All tasks ran on a single node - check cluster configuration")
    
    return node_distribution

def main():
    """Main test function"""
    logger.info("Starting Ray Cluster Health Test")
    logger.info("This test will run for 5 minutes to verify cluster functionality")
    
    try:
        # Initialize Ray (connect to existing cluster)
        logger.info("Connecting to Ray cluster...")
        ray.init(address='auto')
        
        # Get initial cluster information
        cluster_resources, nodes = get_cluster_info()
        
        if not cluster_resources:
            logger.error("Failed to get cluster information")
            return False
        
        # Check if we have worker nodes
        if len(nodes) < 2:
            logger.warning(f"Only {len(nodes)} node(s) detected. Expected head + worker nodes.")
        
        # Run the distributed workload
        results = run_distributed_workload()
        
        # Analyze results
        node_distribution = analyze_results(results)
        
        # Final cluster status check
        logger.info("=== FINAL CLUSTER STATUS ===")
        final_resources, final_nodes = get_cluster_info()
        
        # Generate summary report
        logger.info("=== TEST SUMMARY ===")
        total_tasks = sum(len(tasks) for tasks in results.values())
        logger.info(f"Total tasks completed: {total_tasks}")
        logger.info(f"Nodes utilized: {len(node_distribution)}")
        
        if total_tasks > 0 and len(node_distribution) > 1:
            logger.info("🎉 CLUSTER TEST PASSED: All worker nodes are functioning properly!")
            return True
        else:
            logger.error("❌ CLUSTER TEST FAILED: Issues detected with cluster configuration")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False
    
    finally:
        try:
            ray.shutdown()
            logger.info("Ray shutdown completed")
        except:
            pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 