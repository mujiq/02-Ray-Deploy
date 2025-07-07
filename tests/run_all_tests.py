#!/usr/bin/env python3
"""
Master Test Runner for Ray Cluster

This script orchestrates the execution of all tests in the proper sequence.
It can run individual test categories or all tests in the recommended order.
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path

# Test categories and their execution order
TEST_CATEGORIES = {
    'validation': {
        'order': 1,
        'description': 'Configuration and version validation tests',
        'tests': ['validate_cluster_versions.py']
    },
    'docker': {
        'order': 2, 
        'description': 'Docker configuration and container tests',
        'tests': ['test-docker.yml']
    },
    'cluster': {
        'order': 3,
        'description': 'Ray cluster functionality and performance tests',
        'tests': ['quick_test.py', 'detailed_test.py', 'simple_cluster_test.py']
    },
    'benchmark': {
        'order': 4,
        'description': 'Performance benchmarking tests (future)',
        'tests': []
    }
}

class TestRunner:
    def __init__(self, verbose=False, dry_run=False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.results = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_command(self, command, cwd=None):
        """Execute a command and return results"""
        if self.verbose:
            self.log(f"Executing: {command}")
            
        if self.dry_run:
            self.log(f"DRY RUN: Would execute: {command}")
            return True, "DRY RUN - Not executed", ""
            
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Test timed out after 5 minutes"
        except Exception as e:
            return False, "", str(e)
    
    def run_python_test(self, test_file, category):
        """Run a Python test file"""
        test_path = self.test_dir / category / test_file
        
        if not test_path.exists():
            return False, "", f"Test file not found: {test_path}"
            
        if category == 'cluster':
            # Cluster tests need to run inside Ray container
            copy_cmd = f"sudo docker cp {test_path} ray_head:/tmp/"
            exec_cmd = f"sudo docker exec ray_head python /tmp/{test_file}"
            
            # Copy test to container
            success, stdout, stderr = self.run_command(copy_cmd)
            if not success:
                return False, stdout, f"Failed to copy test: {stderr}"
                
            # Execute test in container
            return self.run_command(exec_cmd)
        else:
            # Run validation tests locally
            return self.run_command(f"python3 {test_path}")
    
    def run_ansible_test(self, test_file, category):
        """Run an Ansible playbook test"""
        test_path = self.test_dir / category / test_file
        
        if not test_path.exists():
            return False, "", f"Test file not found: {test_path}"
            
        return self.run_command(f"ansible-playbook {test_path}")
    
    def run_single_test(self, test_file, category):
        """Run a single test file"""
        self.log(f"Running {category}/{test_file}")
        
        if test_file.endswith('.py'):
            success, stdout, stderr = self.run_python_test(test_file, category)
        elif test_file.endswith('.yml') or test_file.endswith('.yaml'):
            success, stdout, stderr = self.run_ansible_test(test_file, category)
        else:
            return False, "", f"Unknown test file type: {test_file}"
        
        result = {
            'test': f"{category}/{test_file}",
            'success': success,
            'stdout': stdout,
            'stderr': stderr,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        if success:
            self.log(f"✅ PASSED: {category}/{test_file}")
        else:
            self.log(f"❌ FAILED: {category}/{test_file}")
            if self.verbose:
                self.log(f"Error: {stderr}")
                
        return success, stdout, stderr
    
    def run_category(self, category):
        """Run all tests in a category"""
        if category not in TEST_CATEGORIES:
            self.log(f"Unknown test category: {category}", "ERROR")
            return False
            
        cat_info = TEST_CATEGORIES[category]
        self.log(f"Running {category} tests: {cat_info['description']}")
        
        if not cat_info['tests']:
            self.log(f"No tests defined for category: {category}")
            return True
            
        all_passed = True
        for test_file in cat_info['tests']:
            success, _, _ = self.run_single_test(test_file, category)
            if not success:
                all_passed = False
                
        return all_passed
    
    def run_all_tests(self):
        """Run all tests in the recommended order"""
        self.log("Starting comprehensive test suite execution")
        
        # Sort categories by execution order
        sorted_categories = sorted(
            TEST_CATEGORIES.keys(),
            key=lambda x: TEST_CATEGORIES[x]['order']
        )
        
        overall_success = True
        for category in sorted_categories:
            if not self.run_category(category):
                overall_success = False
                self.log(f"Category {category} had test failures", "WARNING")
        
        return overall_success
    
    def generate_report(self):
        """Generate a test execution report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'execution_time': datetime.now().isoformat()
            },
            'results': self.results
        }
        
        # Save to file
        report_file = self.project_root / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"Test report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("TEST EXECUTION SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  ❌ {result['test']}")
        
        return report

def main():
    parser = argparse.ArgumentParser(description="Ray Cluster Test Runner")
    parser.add_argument('--category', choices=list(TEST_CATEGORIES.keys()),
                       help='Run tests for specific category only')
    parser.add_argument('--test', help='Run specific test file (must specify --category)')
    parser.add_argument('--list', action='store_true', help='List all available tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be executed')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available test categories and tests:")
        for category, info in sorted(TEST_CATEGORIES.items(), key=lambda x: x[1]['order']):
            print(f"\n{info['order']}. {category}: {info['description']}")
            for test in info['tests']:
                print(f"   - {test}")
        return
    
    runner = TestRunner(verbose=args.verbose, dry_run=args.dry_run)
    
    try:
        if args.test and args.category:
            # Run specific test
            success, _, _ = runner.run_single_test(args.test, args.category)
            sys.exit(0 if success else 1)
        elif args.category:
            # Run category
            success = runner.run_category(args.category)
            sys.exit(0 if success else 1)
        else:
            # Run all tests
            success = runner.run_all_tests()
            report = runner.generate_report()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        runner.log("Test execution interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        runner.log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main() 