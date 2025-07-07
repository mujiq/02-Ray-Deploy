# Ray Cluster Tests

This directory contains all testing and validation scripts for the Ray cluster deployment project.

## Test Structure

```
tests/
├── cluster/          # Ray cluster functionality tests
├── docker/           # Docker-related tests
├── validation/       # Configuration and version validation
├── benchmark/        # Performance and benchmark tests (future)
└── README.md        # This file
```

## Test Categories

### 🔧 Cluster Tests (`tests/cluster/`)

These tests verify Ray cluster functionality, performance, and distributed computing capabilities.

| Test File | Description | Usage |
|-----------|-------------|-------|
| `quick_test.py` | Fast cluster connectivity and basic functionality test | Quick health check |
| `detailed_test.py` | Comprehensive test with task distribution analysis | Full cluster validation |
| `simple_cluster_test.py` | Simple 5-minute cluster stress test | Endurance testing |
| `test_ray_cluster.py` | Original comprehensive cluster test suite | Legacy comprehensive test |

#### Running Cluster Tests

**Inside Ray Container:**
```bash
# Copy test to Ray head container
sudo docker cp tests/cluster/quick_test.py ray_head:/tmp/
sudo docker exec ray_head python /tmp/quick_test.py

# For detailed testing
sudo docker cp tests/cluster/detailed_test.py ray_head:/tmp/
sudo docker exec ray_head python /tmp/detailed_test.py
```

**Expected Results:**
- All nodes should be detected and responsive
- Task distribution across worker nodes
- Consistent Python/Ray versions
- Performance metrics within expected ranges

### 🐳 Docker Tests (`tests/docker/`)

Tests for Docker configuration and container health.

| Test File | Description | Usage |
|-----------|-------------|-------|
| `test-docker.yml` | Ansible playbook to test Docker installation | Container verification |

#### Running Docker Tests

```bash
ansible-playbook tests/docker/test-docker.yml
```

### ✅ Validation Tests (`tests/validation/`)

Scripts for validating configuration, versions, and deployment status.

| Test File | Description | Usage |
|-----------|-------------|-------|
| `validate_cluster_versions.py` | Validates Ray/Python version consistency | Version verification |
| `validate_checkpoint.py` | Validates modular deployment checkpoints | Deployment validation |

#### Running Validation Tests

```bash
# Version validation
python3 tests/validation/validate_cluster_versions.py

# Checkpoint validation (if using modular deployment)
python3 tests/validation/validate_checkpoint.py --checkpoint <checkpoint_name>
```

### 📊 Benchmark Tests (`tests/benchmark/`)

*Reserved for future performance benchmarking tests*

## Master Test Runner

A comprehensive test runner script is available to orchestrate all tests:

```bash
# Run all tests in recommended order
python3 tests/run_all_tests.py

# List all available tests
python3 tests/run_all_tests.py --list

# Run specific category
python3 tests/run_all_tests.py --category cluster

# Run specific test
python3 tests/run_all_tests.py --category validation --test validate_cluster_versions.py

# Dry run (show what would be executed)
python3 tests/run_all_tests.py --dry-run

# Verbose output
python3 tests/run_all_tests.py --verbose
```

The test runner automatically:
- ✅ Executes tests in proper order (validation → docker → cluster → benchmark)
- ✅ Handles container-based tests for cluster category
- ✅ Generates comprehensive test reports
- ✅ Provides detailed error reporting
- ✅ Supports individual test execution

## Test Execution Guidelines

### Prerequisites

1. **Ray Cluster Running:** Ensure Ray cluster is deployed and operational
2. **Network Access:** Validate connectivity to all cluster nodes
3. **Proper Permissions:** Run tests with appropriate sudo/user permissions

### Test Sequence Recommendations

1. **Docker Tests First:**
   ```bash
   ansible-playbook tests/docker/test-docker.yml
   ```

2. **Version Validation:**
   ```bash
   python3 tests/validation/validate_cluster_versions.py
   ```

3. **Quick Cluster Test:**
   ```bash
   sudo docker cp tests/cluster/quick_test.py ray_head:/tmp/
   sudo docker exec ray_head python /tmp/quick_test.py
   ```

4. **Detailed Performance Test:**
   ```bash
   sudo docker cp tests/cluster/detailed_test.py ray_head:/tmp/
   sudo docker exec ray_head python /tmp/detailed_test.py
   ```

### Expected Test Results

✅ **Successful Test Indicators:**
- All nodes detected and responsive
- Version consistency across cluster
- Efficient task distribution
- No container health issues
- Performance within expected ranges

❌ **Common Issues:**
- **Version Mismatches:** Run `ansible-playbook sync-versions.yml`
- **Node Connectivity:** Check network and firewall settings
- **Container Issues:** Run `ansible-playbook cleanup-cluster.yml` and redeploy
- **Performance Problems:** Verify resource allocation and network latency

## Integration with CI/CD

These tests can be integrated into automated deployment pipelines:

```bash
# Basic validation pipeline
ansible-playbook tests/docker/test-docker.yml
python3 tests/validation/validate_cluster_versions.py
sudo docker exec ray_head python /tmp/quick_test.py
```

## Contributing New Tests

When adding new tests:

1. **Choose Appropriate Directory:** Place in correct category (cluster/docker/validation/benchmark)
2. **Follow Naming Convention:** Use descriptive names with `test_` prefix for Python files
3. **Include Documentation:** Add test description and usage instructions
4. **Error Handling:** Implement proper error handling and meaningful output
5. **Update README:** Document new tests in this file

## Troubleshooting

### Common Test Failures

1. **Ray Connection Issues:**
   - Verify Ray cluster is running: `sudo docker exec ray_head ray status`
   - Check network connectivity between nodes

2. **Permission Errors:**
   - Run tests with appropriate sudo privileges
   - Verify user is in docker group

3. **Version Inconsistencies:**
   - Run version synchronization: `ansible-playbook sync-versions.yml`
   - Clean and redeploy if necessary: `ansible-playbook cleanup-cluster.yml`

4. **Performance Issues:**
   - Check system resources: CPU, memory, disk usage
   - Verify network latency between nodes
   - Review cluster configuration

For additional help, refer to the main project documentation or cluster status reports. 