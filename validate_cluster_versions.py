#!/usr/bin/env python3
"""
Ray Cluster Version Validation Script
This script validates version consistency across the Ray cluster
and ensures the client has compatible versions before running tests.
"""

import subprocess
import sys
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def get_client_ray_version():
    """Get the Ray version installed in the current Python environment"""
    try:
        import ray
        return ray.__version__
    except ImportError:
        return None

def get_client_python_version():
    """Get the current Python version"""
    return f"{sys.version_info.major}.{sys.version_info.minor}"

def get_cluster_versions():
    """Get Ray and Python versions from cluster nodes"""
    logger.info("Checking cluster versions...")
    
    # Read inventory to get node IPs
    inventory_file = Path("inventory.ini")
    if not inventory_file.exists():
        logger.error("inventory.ini not found")
        return None
    
    # Get cluster configuration
    success, output, error = run_command("ansible ray_cluster -m setup | grep ansible_host")
    if not success:
        logger.error(f"Failed to get cluster info: {error}")
        return None
    
    cluster_versions = {}
    
    # Check each node's version info
    success, output, error = run_command("ansible ray_cluster -m slurp -a 'src=/home/gpadmin/ray_temp/version_info.env'")
    if success:
        logger.info("Found version info files on cluster nodes")
        # Parse the output to extract version information
        for line in output.split('\n'):
            if 'RAY_VERSION=' in line:
                match = re.search(r'RAY_VERSION=([^\s"]+)', line)
                if match:
                    cluster_versions['ray_version'] = match.group(1)
            if 'PYTHON_VERSION=' in line:
                match = re.search(r'PYTHON_VERSION=([^\s"]+)', line)
                if match:
                    cluster_versions['python_version'] = match.group(1)
    
    return cluster_versions

def check_ray_container_versions():
    """Check Ray container versions directly"""
    logger.info("Checking Ray container versions...")
    
    # Check Ray head container
    success, output, error = run_command("ansible head_nodes -m shell -a 'docker inspect ray_head --format=\"{{.Config.Image}}\"'")
    if success:
        head_image = output.split('\n')[-2].strip() if output else "unknown"
        logger.info(f"Ray head container image: {head_image}")
    
    # Check Ray worker containers
    success, output, error = run_command("ansible worker_nodes -m shell -a 'docker inspect ray_worker --format=\"{{.Config.Image}}\"'")
    if success:
        worker_images = [line.strip() for line in output.split('\n') if 'rayproject/ray:' in line]
        logger.info(f"Ray worker container images: {worker_images}")
        
        # Check if all images are the same
        unique_images = set(worker_images)
        if head_image != "unknown":
            unique_images.add(head_image)
        
        if len(unique_images) == 1:
            logger.info("✅ All Ray containers use the same image version")
            return list(unique_images)[0]
        else:
            logger.warning(f"⚠️  Inconsistent Ray container versions: {unique_images}")
            return None
    
    return None

def install_matching_ray_version(target_version):
    """Install the Ray version that matches the cluster"""
    logger.info(f"Installing Ray version {target_version} to match cluster...")
    
    # Uninstall current Ray
    success, output, error = run_command("python3 -m pip uninstall ray -y")
    if success:
        logger.info("Uninstalled existing Ray version")
    
    # Install matching version
    success, output, error = run_command(f"python3 -m pip install ray=={target_version}")
    if success:
        logger.info(f"✅ Successfully installed Ray {target_version}")
        return True
    else:
        logger.error(f"❌ Failed to install Ray {target_version}: {error}")
        return False

def main():
    """Main validation function"""
    logger.info("🔍 Starting Ray Cluster Version Validation")
    logger.info("=" * 50)
    
    # Get client versions
    client_ray_version = get_client_ray_version()
    client_python_version = get_client_python_version()
    
    logger.info(f"Client Ray version: {client_ray_version or 'Not installed'}")
    logger.info(f"Client Python version: {client_python_version}")
    
    # Check cluster container versions
    cluster_image = check_ray_container_versions()
    if cluster_image:
        # Extract Ray version from Docker image
        if ':' in cluster_image:
            cluster_ray_version = cluster_image.split(':')[1]
            logger.info(f"Cluster Ray version: {cluster_ray_version}")
            
            # Check if versions match
            if client_ray_version == cluster_ray_version:
                logger.info("✅ Client and cluster Ray versions match!")
                return True
            else:
                logger.warning(f"⚠️  Version mismatch - Client: {client_ray_version}, Cluster: {cluster_ray_version}")
                
                # Try to install matching version
                if install_matching_ray_version(cluster_ray_version):
                    logger.info("✅ Version synchronization complete!")
                    return True
                else:
                    logger.error("❌ Failed to synchronize versions")
                    return False
    
    # Fallback: Try to get versions from configuration files
    logger.info("Checking cluster configuration files...")
    cluster_versions = get_cluster_versions()
    
    if cluster_versions:
        target_ray_version = cluster_versions.get('ray_version')
        target_python_version = cluster_versions.get('python_version')
        
        logger.info(f"Target cluster Ray version: {target_ray_version}")
        logger.info(f"Target cluster Python version: {target_python_version}")
        
        # Check Python version compatibility
        if target_python_version and not client_python_version.startswith(target_python_version):
            logger.warning(f"⚠️  Python version mismatch - Client: {client_python_version}, Target: {target_python_version}")
            logger.warning("Consider using a Python environment that matches the cluster")
        
        # Install matching Ray version if needed
        if target_ray_version and client_ray_version != target_ray_version:
            if install_matching_ray_version(target_ray_version):
                logger.info("✅ Version synchronization complete!")
                return True
            else:
                logger.error("❌ Failed to synchronize versions")
                return False
    
    logger.error("❌ Could not determine cluster versions")
    logger.info("Try running: ansible-playbook sync-versions.yml")
    return False

if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("🎉 Cluster is ready for testing!")
        logger.info("You can now run: python3 test_ray_cluster.py")
    else:
        logger.error("❌ Version validation failed")
        logger.info("Run 'ansible-playbook sync-versions.yml' to fix version issues")
    
    sys.exit(0 if success else 1) 