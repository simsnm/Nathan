#!/usr/bin/env python3
"""
Simple workflow runner for codechat - chains multiple agent calls
"""

import os
import sys
import yaml
import subprocess
import json
from pathlib import Path

def validate_workflow(workflow):
    """Validate workflow to prevent security issues"""
    valid_roles = ['clarifier', 'architect', 'coder', 'reviewer', 'tester', 'documenter', 'optimizer', 'researcher']
    
    for step in workflow.get('steps', []):
        # Validate role
        if 'role' in step and step['role'] not in valid_roles:
            raise ValueError(f"Invalid role: {step['role']}")
        
        # Validate no shell commands
        if any(danger in str(step).lower() for danger in ['exec', 'eval', 'os.system', '__import__']):
            raise ValueError("Potential code execution detected in workflow")
            
        # Validate file paths don't escape
        for field in ['input', 'output']:
            if field in step and '..' in str(step[field]):
                raise ValueError(f"Path traversal detected in {field}")
    
    return True

def run_workflow(workflow_file, api_key=None):
    """Run a workflow of multiple agent steps"""
    
    # Load workflow with safe loader
    with open(workflow_file, 'r') as f:
        workflow = yaml.safe_load(f)
    
    # Validate before running
    try:
        validate_workflow(workflow)
    except ValueError as e:
        print(f"ERROR: Invalid workflow - {e}", file=sys.stderr)
        return False
    
    print(f"Running workflow: {workflow['name']}")
    print("-" * 50)
    
    # Keep conversation context across steps
    context_file = f"{workflow_file}.context.json"
    
    # Check for planning-first enforcement
    first_step = workflow['steps'][0] if workflow['steps'] else None
    if first_step and first_step.get('role') == 'coder':
        print("WARNING: Workflow starts with 'coder' role without architect/planning step!")
        print("Consider adding an architect step first for better results.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    for i, step in enumerate(workflow['steps'], 1):
        print(f"\nStep {i}: {step.get('role', 'default')} role")
        print(f"Prompt: {step['prompt'][:100]}...")
        
        # Build command
        cmd = ['python3', 'codechat.py', step['prompt']]
        
        # Add skip-planning flag if explicitly set in workflow
        if step.get('skip_planning'):
            cmd.append('--skip-planning')
        
        # Auto-add documentation step after coder
        if step.get('role') == 'coder' and workflow.get('auto_document', False):
            # Mark this step for auto-documentation
            cmd.append('--auto-doc')
        
        # Add role
        if 'role' in step:
            cmd.extend(['-r', step['role']])
        
        # Add input file if specified
        if 'input' in step:
            cmd.extend(['-f', step['input']])
        
        # Add output file if specified
        if 'output' in step:
            cmd.extend(['-o', step['output']])
            if step.get('code_only'):
                cmd.append('--code-only')
        
        # Add context to maintain conversation
        cmd.extend(['-c', context_file])
        
        # Add API key if provided
        if api_key:
            cmd.extend(['--api-key', api_key])
        
        # Run the command
        print(f"Running: {' '.join(cmd[:5])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error in step {i}:")
            print(result.stderr)
            return False
        
        print(result.stdout)
        
        if 'output' in step:
            print(f"Output saved to: {step['output']}")
    
    print("\n" + "=" * 50)
    print("Workflow completed successfully!")
    
    # List generated files
    outputs = [step.get('output') for step in workflow['steps'] if 'output' in step]
    if outputs:
        print("\nGenerated files:")
        for output in outputs:
            if os.path.exists(output):
                size = os.path.getsize(output)
                print(f"  - {output} ({size} bytes)")
    
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run a multi-agent workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example workflow.yaml:
  name: "Build API"
  steps:
    - role: architect
      prompt: "Design a REST API"
      output: design.md
    - role: coder
      prompt: "Implement it"
      input: design.md
      output: api.py
      code_only: true
        """
    )
    
    parser.add_argument('workflow', help='YAML workflow file')
    parser.add_argument('--api-key', help='API key to use')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.workflow):
        print(f"Error: Workflow file not found: {args.workflow}", file=sys.stderr)
        sys.exit(1)
    
    success = run_workflow(args.workflow, args.api_key)
    sys.exit(0 if success else 1)