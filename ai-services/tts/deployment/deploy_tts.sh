#!/bin/bash
# Deploy TTS Service on Ray Cluster
# Usage: ./deploy_tts.sh [options]

set -e

# Default configuration
RAY_ADDRESS="auto"
SERVICE_PORT=8000
INSTALL_DEPS=false
SERVICE_NAME="tts-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
🎵 Ray TTS Service Deployment Script 🎵

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -a, --ray-address ADDR  Ray cluster address (default: auto)
    -p, --port PORT         Service port (default: 8000)
    -i, --install-deps      Install Python dependencies
    -n, --name NAME         Service name (default: tts-service)
    --check-cluster         Check Ray cluster status only
    --stop-service          Stop the TTS service
    --test-service          Test the deployed service

EXAMPLES:
    $0                      # Deploy with defaults
    $0 -i                   # Install deps and deploy
    $0 -p 8080              # Deploy on port 8080
    $0 --check-cluster      # Check cluster status
    $0 --test-service       # Test deployment

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--ray-address)
            RAY_ADDRESS="$2"
            shift 2
            ;;
        -p|--port)
            SERVICE_PORT="$2"
            shift 2
            ;;
        -i|--install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        -n|--name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --check-cluster)
            CHECK_ONLY=true
            shift
            ;;
        --stop-service)
            STOP_SERVICE=true
            shift
            ;;
        --test-service)
            TEST_SERVICE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if Python 3 is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python version: $python_version"
}

# Check Ray cluster status
check_ray_cluster() {
    log_info "Checking Ray cluster status..."
    
    python3 -c "
import ray
try:
    ray.init(address='$RAY_ADDRESS', ignore_reinit_error=True)
    cluster_info = ray.cluster_resources()
    print(f'✅ Ray cluster connected successfully')
    print(f'Available CPUs: {cluster_info.get(\"CPU\", 0)}')
    print(f'Available GPUs: {cluster_info.get(\"GPU\", 0)}')
    print(f'Available memory: {cluster_info.get(\"memory\", 0)/1e9:.1f} GB')
    ray.shutdown()
except Exception as e:
    print(f'❌ Failed to connect to Ray cluster: {e}')
    exit(1)
"
    if [ $? -ne 0 ]; then
        log_error "Ray cluster check failed"
        exit 1
    fi
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ ! -f "deployment/requirements_tts.txt" ]; then
        log_error "deployment/requirements_tts.txt not found"
        exit 1
    fi
    
    python3 -m pip install -r deployment/requirements_tts.txt
    
    if [ $? -eq 0 ]; then
        log_success "Dependencies installed successfully"
    else
        log_error "Failed to install dependencies"
        exit 1
    fi
}

# Stop existing service
stop_service() {
    log_info "Stopping TTS service..."
    
    python3 -c "
import ray
from ray import serve
try:
    ray.init(address='$RAY_ADDRESS', ignore_reinit_error=True)
    serve.delete('$SERVICE_NAME')
    print('✅ TTS service stopped')
    ray.shutdown()
except Exception as e:
    print(f'Service may not be running: {e}')
"
}

# Deploy the TTS service
deploy_service() {
    log_info "Deploying TTS service..."
    
    if [ ! -f "deployment/deploy_tts_service.py" ]; then
        log_error "deployment/deploy_tts_service.py not found"
        exit 1
    fi
    
    # Run deployment in background
    python3 deployment/deploy_tts_service.py \
        --ray-address "$RAY_ADDRESS" \
        --port "$SERVICE_PORT" &
    
    local deploy_pid=$!
    
    # Wait a bit for deployment to start
    sleep 5
    
    # Check if deployment is still running
    if kill -0 $deploy_pid 2>/dev/null; then
        log_success "TTS service deployment started (PID: $deploy_pid)"
        log_info "Service will be available at: http://0.0.0.0:$SERVICE_PORT"
        log_info "API documentation: http://0.0.0.0:$SERVICE_PORT/docs"
        log_info "Health check: curl http://0.0.0.0:$SERVICE_PORT/health"
        
        # Save PID for later reference
        echo $deploy_pid > tts_service.pid
        
        return 0
    else
        log_error "TTS service deployment failed"
        return 1
    fi
}

# Test the deployed service
test_service() {
    log_info "Testing TTS service..."
    
    local max_retries=30
    local retry_count=0
    
    # Wait for service to be ready
    while [ $retry_count -lt $max_retries ]; do
        if curl -s "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
            log_success "Service is responding"
            break
        fi
        
        retry_count=$((retry_count + 1))
        log_info "Waiting for service... ($retry_count/$max_retries)"
        sleep 2
    done
    
    if [ $retry_count -eq $max_retries ]; then
        log_error "Service did not become ready in time"
        return 1
    fi
    
    # Run basic health check
    log_info "Running health check..."
    local health_response=$(curl -s "http://localhost:$SERVICE_PORT/health")
    echo "$health_response" | python3 -m json.tool
    
    # Test basic synthesis
    log_info "Testing basic synthesis..."
    local test_response=$(curl -s -X POST "http://localhost:$SERVICE_PORT/synthesize" \
        -H "Content-Type: application/json" \
        -d '{"text": "Hello, this is a test of the TTS service!", "emotion": "happy"}')
    
    if echo "$test_response" | grep -q "duration"; then
        log_success "Basic synthesis test passed"
        echo "$test_response" | python3 -m json.tool
    else
        log_error "Basic synthesis test failed"
        echo "$test_response"
        return 1
    fi
    
    log_success "All tests passed! 🎉"
}

# Main execution
main() {
    echo "🎵 Ray TTS Service Deployment 🎵"
    echo "=================================="
    
    # Check Python
    check_python
    
    # Handle special operations
    if [ "$CHECK_ONLY" = true ]; then
        check_ray_cluster
        exit 0
    fi
    
    if [ "$STOP_SERVICE" = true ]; then
        stop_service
        exit 0
    fi
    
    if [ "$TEST_SERVICE" = true ]; then
        test_service
        exit 0
    fi
    
    # Normal deployment flow
    check_ray_cluster
    
    if [ "$INSTALL_DEPS" = true ]; then
        install_dependencies
    fi
    
    # Stop existing service if running
    stop_service
    
    # Deploy new service
    if deploy_service; then
        log_info "Waiting for service to be ready..."
        sleep 10
        
        # Test the deployment
        if test_service; then
            echo ""
            echo "🎉 TTS Service Deployment Complete! 🎉"
            echo "======================================"
            echo "Service URL: http://0.0.0.0:$SERVICE_PORT"
            echo "API Docs: http://0.0.0.0:$SERVICE_PORT/docs"
            echo "Health: curl http://0.0.0.0:$SERVICE_PORT/health"
            echo ""
            echo "Example usage:"
            echo "curl -X POST http://0.0.0.0:$SERVICE_PORT/synthesize \\"
            echo "  -H 'Content-Type: application/json' \\"
            echo "  -d '{\"text\": \"Hello world!\", \"emotion\": \"happy\"}'"
            echo ""
            echo "To stop the service: $0 --stop-service"
            echo "To test the service: $0 --test-service"
        else
            log_error "Service deployment verification failed"
            exit 1
        fi
    else
        log_error "Service deployment failed"
        exit 1
    fi
}

# Execute main function
main "$@" 