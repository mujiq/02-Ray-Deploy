#!/bin/bash

# =============================================================================
# Enterprise Translation Service Deployment Script
# =============================================================================
# Features:
# - Multi-model translation deployment (NLLB-200, UMT5-XXL, Babel-83B)
# - Ray cluster health verification
# - Automated dependency installation
# - Service monitoring and health checks
# - Redundancy and auto-scaling configuration
# - Comprehensive logging and error handling
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SERVICE_NAME="translation-service"
DEFAULT_PORT=8001
DEFAULT_RAY_ADDRESS="ray://192.168.40.240:10001"
LOG_FILE="/tmp/${SERVICE_NAME}-deploy.log"
PID_FILE="/tmp/${SERVICE_NAME}.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_header() {
    echo -e "${PURPLE}[==========]${NC} $1 ${PURPLE}[==========]${NC}" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
Enterprise Translation Service Deployment Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --install-deps          Install Python dependencies
    --port PORT            Service port (default: $DEFAULT_PORT)
    --ray-address ADDR     Ray cluster address (default: $DEFAULT_RAY_ADDRESS)
    --check-cluster        Check Ray cluster health only
    --stop                 Stop running service
    --restart              Restart service
    --status               Check service status
    --logs                 Show service logs
    --test                 Run service tests after deployment
    --help                 Show this help message

EXAMPLES:
    # Deploy with dependency installation
    $0 --install-deps --port 8001

    # Check cluster health
    $0 --check-cluster

    # Deploy and test
    $0 --install-deps --test

    # Restart service
    $0 --restart

FEATURES:
    ✓ Multi-model translation (NLLB-200, UMT5-XXL, Babel-83B)
    ✓ 200+ language support with auto-model selection
    ✓ Redundancy across Ray cluster nodes
    ✓ Auto-scaling (2-8 replicas total)
    ✓ Language detection and validation
    ✓ Performance monitoring and health checks
    ✓ Graceful failover between models

ENDPOINTS:
    http://HOST:PORT/docs        - API documentation
    http://HOST:PORT/health      - Health check
    http://HOST:PORT/translate   - Translation endpoint
    http://HOST:PORT/detect-language - Language detection
    http://HOST:PORT/languages   - Supported languages
    http://HOST:PORT/models      - Model information

EOF
}

# Parse command line arguments
INSTALL_DEPS=false
SERVICE_PORT=$DEFAULT_PORT
RAY_ADDRESS=$DEFAULT_RAY_ADDRESS
CHECK_CLUSTER_ONLY=false
STOP_SERVICE=false
RESTART_SERVICE=false
CHECK_STATUS=false
SHOW_LOGS=false
RUN_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --port)
            SERVICE_PORT="$2"
            shift 2
            ;;
        --ray-address)
            RAY_ADDRESS="$2"
            shift 2
            ;;
        --check-cluster)
            CHECK_CLUSTER_ONLY=true
            shift
            ;;
        --stop)
            STOP_SERVICE=true
            shift
            ;;
        --restart)
            RESTART_SERVICE=true
            shift
            ;;
        --status)
            CHECK_STATUS=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Initialize log
echo "$(date): Starting translation service deployment" > "$LOG_FILE"

# Function to check if Ray cluster is available
check_ray_cluster() {
    log_info "Checking Ray cluster connectivity..."
    
    python3 -c "
import ray
import sys
try:
    ray.init(address='$RAY_ADDRESS', ignore_reinit_error=True)
    cluster_info = ray.cluster_resources()
    total_cpus = cluster_info.get('CPU', 0)
    total_gpus = cluster_info.get('GPU', 0)
    total_memory = cluster_info.get('memory', 0) / (1024**3)  # Convert to GB
    
    print(f'✓ Ray cluster connected successfully')
    print(f'✓ Total CPUs: {int(total_cpus)}')
    print(f'✓ Total GPUs: {int(total_gpus)}') 
    print(f'✓ Total Memory: {total_memory:.1f} GB')
    
    # Check if we have enough resources for translation models
    if total_cpus < 16:
        print(f'⚠  Warning: Limited CPU resources ({int(total_cpus)}). Recommend 16+ CPUs for optimal performance.')
    if total_gpus < 2:
        print(f'⚠  Warning: Limited GPU resources ({int(total_gpus)}). Recommend 2+ GPUs for optimal performance.')
    if total_memory < 32:
        print(f'⚠  Warning: Limited memory ({total_memory:.1f} GB). Recommend 32+ GB for large models.')
    
    ray.shutdown()
    sys.exit(0)
except Exception as e:
    print(f'✗ Ray cluster connection failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "Ray cluster is healthy and ready"
        return 0
    else
        log_error "Ray cluster connection failed"
        return 1
    fi
}

# Function to install dependencies
install_dependencies() {
    log_header "Installing Dependencies"
    
    if [ ! -f "deployment/requirements_translation.txt" ]; then
        log_error "requirements_translation.txt not found"
        exit 1
    fi
    
    log_info "Installing Python dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r deployment/requirements_translation.txt
    
    # Install system dependencies if needed
    if command -v apt-get >/dev/null 2>&1; then
        log_info "Installing system dependencies (Ubuntu/Debian)..."
        sudo apt-get update -qq
        sudo apt-get install -y libicu-dev libffi-dev python3-dev build-essential
    elif command -v yum >/dev/null 2>&1; then
        log_info "Installing system dependencies (CentOS/RHEL)..."
        sudo yum install -y libicu-devel libffi-devel python3-devel gcc gcc-c++ make
    fi
    
    log_success "Dependencies installed successfully"
}

# Function to stop the service
stop_service() {
    log_header "Stopping Translation Service"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_info "Stopping service (PID: $PID)..."
            kill -TERM "$PID"
            sleep 5
            
            if kill -0 "$PID" 2>/dev/null; then
                log_warning "Service didn't stop gracefully, forcing shutdown..."
                kill -KILL "$PID"
            fi
            
            rm -f "$PID_FILE"
            log_success "Service stopped successfully"
        else
            log_warning "Service not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        log_info "Service not running (no PID file)"
    fi
    
    # Also try to kill by name
    pkill -f "translation_service.py" || true
    
    # Clean up Ray serve deployments
    python3 -c "
import ray
try:
    ray.init(address='$RAY_ADDRESS', ignore_reinit_error=True)
    from ray import serve
    serve.shutdown()
    ray.shutdown()
    print('Ray Serve shutdown completed')
except:
    pass
" 2>/dev/null || true
}

# Function to check service status
check_service_status() {
    log_header "Service Status Check"
    
    # Check if PID file exists and process is running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log_success "Service is running (PID: $PID)"
            
            # Check if service is responding
            if curl -s "http://localhost:$SERVICE_PORT/health" >/dev/null 2>&1; then
                log_success "Service is responding on port $SERVICE_PORT"
                
                # Get detailed health info
                log_info "Service health details:"
                curl -s "http://localhost:$SERVICE_PORT/health" | python3 -m json.tool 2>/dev/null || echo "  Health check response received"
                
            else
                log_warning "Service is running but not responding on port $SERVICE_PORT"
            fi
        else
            log_error "Service not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        log_warning "Service not running (no PID file)"
    fi
    
    # Check Ray deployments
    log_info "Checking Ray Serve deployments..."
    python3 -c "
import ray
from ray import serve
try:
    ray.init(address='$RAY_ADDRESS', ignore_reinit_error=True)
    deployments = serve.list_deployments()
    if deployments:
        print('Active Ray Serve deployments:')
        for name, status in deployments.items():
            print(f'  - {name}: {status}')
    else:
        print('No active Ray Serve deployments')
    ray.shutdown()
except Exception as e:
    print(f'Error checking deployments: {e}')
" 2>/dev/null || log_warning "Could not check Ray Serve status"
}

# Function to show logs
show_service_logs() {
    log_header "Service Logs"
    
    if [ -f "$LOG_FILE" ]; then
        log_info "Recent deployment logs:"
        tail -n 50 "$LOG_FILE"
    else
        log_warning "No deployment log file found"
    fi
    
    # Show Python service logs if available
    if [ -f "/tmp/${SERVICE_NAME}-python.log" ]; then
        log_info "Recent Python service logs:"
        tail -n 50 "/tmp/${SERVICE_NAME}-python.log"
    fi
}

# Function to deploy the service
deploy_service() {
    log_header "Deploying Translation Service"
    
    if [ ! -f "deployment/translation_service.py" ]; then
        log_error "translation_service.py not found"
        exit 1
    fi
    
    # Stop existing service
    stop_service
    
    log_info "Starting translation service on port $SERVICE_PORT..."
    
    # Run deployment in background with logging
    nohup python3 deployment/translation_service.py \
        --ray-address "$RAY_ADDRESS" \
        --port "$SERVICE_PORT" \
        --host "0.0.0.0" \
        > "/tmp/${SERVICE_NAME}-python.log" 2>&1 &
    
    SERVICE_PID=$!
    echo "$SERVICE_PID" > "$PID_FILE"
    
    log_info "Service starting with PID: $SERVICE_PID"
    
    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    for i in {1..60}; do
        if curl -s "http://localhost:$SERVICE_PORT/health" >/dev/null 2>&1; then
            log_success "Service is ready and responding!"
            break
        fi
        
        if ! kill -0 "$SERVICE_PID" 2>/dev/null; then
            log_error "Service process died during startup"
            cat "/tmp/${SERVICE_NAME}-python.log" | tail -n 20
            exit 1
        fi
        
        echo -n "."
        sleep 2
    done
    
    if ! curl -s "http://localhost:$SERVICE_PORT/health" >/dev/null 2>&1; then
        log_error "Service failed to start within 120 seconds"
        log_error "Check logs with: $0 --logs"
        exit 1
    fi
}

# Function to test the service
test_service() {
    log_header "Testing Translation Service"
    
    # Test basic health check
    log_info "Testing health check..."
    if curl -s "http://localhost:$SERVICE_PORT/health" | grep -q "healthy"; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # Test language detection
    log_info "Testing language detection..."
    DETECTION_RESULT=$(curl -s -X POST "http://localhost:$SERVICE_PORT/detect-language" \
        -H "Content-Type: application/json" \
        -d '{"text": "Hello world, this is a test message"}')
    
    if echo "$DETECTION_RESULT" | grep -q "detected_language"; then
        log_success "Language detection test passed"
        log_info "Detection result: $(echo "$DETECTION_RESULT" | python3 -m json.tool 2>/dev/null | head -3)"
    else
        log_warning "Language detection test failed"
    fi
    
    # Test translation
    log_info "Testing translation (English to Spanish)..."
    TRANSLATION_RESULT=$(curl -s -X POST "http://localhost:$SERVICE_PORT/translate" \
        -H "Content-Type: application/json" \
        -d '{"text": "Hello, how are you today?", "source_lang": "en", "target_lang": "es", "model": "auto"}')
    
    if echo "$TRANSLATION_RESULT" | grep -q "translated_text"; then
        log_success "Translation test passed"
        log_info "Translation result: $(echo "$TRANSLATION_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('translated_text', 'N/A'))" 2>/dev/null)"
    else
        log_warning "Translation test failed"
        log_warning "Response: $TRANSLATION_RESULT"
    fi
    
    # Test model info
    log_info "Testing model information endpoint..."
    if curl -s "http://localhost:$SERVICE_PORT/models" | grep -q "models"; then
        log_success "Model information test passed"
    else
        log_warning "Model information test failed"
    fi
    
    # Test supported languages
    log_info "Testing supported languages endpoint..."
    LANGUAGES_RESULT=$(curl -s "http://localhost:$SERVICE_PORT/languages")
    if echo "$LANGUAGES_RESULT" | grep -q "nllb_200"; then
        log_success "Supported languages test passed"
        TOTAL_LANGS=$(echo "$LANGUAGES_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(sum(model['count'] for model in data.values()))" 2>/dev/null)
        log_info "Total supported languages across all models: ${TOTAL_LANGS:-unknown}"
    else
        log_warning "Supported languages test failed"
    fi
    
    log_success "Service testing completed"
}

# Function to run integration tests
run_integration_tests() {
    log_header "Running Integration Tests"
    
    if [ -f "tests/translation_client_examples.py" ]; then
        log_info "Running comprehensive test suite..."
        cd "$SCRIPT_DIR/.."
        python3 tests/translation_client_examples.py --service-url "http://localhost:$SERVICE_PORT"
    else
        log_warning "Test suite not found, running basic tests only"
        test_service
    fi
}

# Main execution
main() {
    log_header "Enterprise Translation Service Deployment"
    log_info "Script started at $(date)"
    log_info "Service port: $SERVICE_PORT"
    log_info "Ray address: $RAY_ADDRESS"
    
    # Handle specific actions
    if [ "$SHOW_LOGS" = true ]; then
        show_service_logs
        exit 0
    fi
    
    if [ "$CHECK_STATUS" = true ]; then
        check_service_status
        exit 0
    fi
    
    if [ "$STOP_SERVICE" = true ]; then
        stop_service
        exit 0
    fi
    
    if [ "$RESTART_SERVICE" = true ]; then
        log_info "Restarting service..."
        stop_service
        sleep 2
        # Continue to deployment
    fi
    
    # Check Ray cluster
    if ! check_ray_cluster; then
        log_error "Ray cluster check failed. Please ensure Ray cluster is running."
        exit 1
    fi
    
    if [ "$CHECK_CLUSTER_ONLY" = true ]; then
        exit 0
    fi
    
    # Install dependencies if requested
    if [ "$INSTALL_DEPS" = true ]; then
        install_dependencies
    fi
    
    # Deploy the service
    deploy_service
    
    # Run tests if requested
    if [ "$RUN_TESTS" = true ]; then
        sleep 5  # Give service a moment to fully initialize
        run_integration_tests
    fi
    
    # Final status
    log_header "Deployment Complete"
    log_success "Translation service deployed successfully!"
    log_info "Service Details:"
    log_info "  • API Documentation: http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT/docs"
    log_info "  • Health Check: http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT/health"
    log_info "  • Translation API: http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT/translate"
    log_info "  • Language Detection: http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT/detect-language"
    log_info ""
    log_info "Models Available:"
    log_info "  • NLLB-200: 200+ languages, state-of-the-art quality"
    log_info "  • UMT5-XXL: 107 languages, excellent multilingual capabilities"
    log_info "  • Babel-83B: 25 languages, highest quality for supported languages"
    log_info ""
    log_info "Features:"
    log_info "  • Automatic model selection based on language pair"
    log_info "  • Redundancy and failover across Ray cluster nodes"
    log_info "  • Auto-scaling from 2-8 replicas based on load"
    log_info "  • Language detection and validation"
    log_info "  • Performance monitoring and health checks"
    log_info ""
    log_info "Management Commands:"
    log_info "  • Status: $0 --status"
    log_info "  • Logs: $0 --logs"
    log_info "  • Stop: $0 --stop"
    log_info "  • Restart: $0 --restart"
    log_info ""
    log_info "Log file: $LOG_FILE"
}

# Run main function
main "$@" 