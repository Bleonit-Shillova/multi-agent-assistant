"""
Evaluation Test Cases
Test questions to verify the system works correctly.
"""

# Test cases with expected behaviors
TEST_CASES = [
    {
        "id": 1,
        "input": "What are the top 3 risks mentioned in the project documents?",
        "expected_behavior": [
            "Should identify risks from the documents",
            "Should cite the source document",
            "Should not invent risks not in documents"
        ],
        "type": "extraction"
    },
    {
        "id": 2,
        "input": "Create a client update email summarizing the weekly progress",
        "expected_behavior": [
            "Should produce email format",
            "Should include information from weekly update",
            "Should have professional tone",
            "Should cite sources"
        ],
        "type": "generation"
    },
    {
        "id": 3,
        "input": "Extract all deadlines and their owners into an action list",
        "expected_behavior": [
            "Should list deadlines with dates",
            "Should include owner names",
            "Should be in action list format",
            "Should cite source document"
        ],
        "type": "extraction"
    },
    {
        "id": 4,
        "input": "What is the CEO's favorite color?",
        "expected_behavior": [
            "Should say information not found",
            "Should NOT make up an answer",
            "Should suggest what info is needed"
        ],
        "type": "not_found"
    },
    {
        "id": 5,
        "input": "Compare the budget status with the timeline status and recommend priorities",
        "expected_behavior": [
            "Should discuss budget from documents",
            "Should discuss timeline from documents",
            "Should make comparison",
            "Should provide recommendation with justification"
        ],
        "type": "analysis"
    },
    {
        "id": 6,
        "input": "Summarize the team performance and suggest improvements",
        "expected_behavior": [
            "Should mention team performance from docs",
            "Should cite sources",
            "Should only suggest improvements based on documented issues"
        ],
        "type": "summary"
    },
    {
        "id": 7,
        "input": "What are the next week's planned activities?",
        "expected_behavior": [
            "Should extract next week plans from weekly update",
            "Should cite the weekly update document",
            "Should list activities clearly"
        ],
        "type": "extraction"
    },
    {
        "id": 8,
        "input": "Draft a Confluence page summarizing the project status",
        "expected_behavior": [
            "Should produce structured document",
            "Should include key project information",
            "Should have sections/headers",
            "Should cite sources"
        ],
        "type": "generation"
    }
]


def run_evaluation():
    """Run all test cases and report results."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from agents.workflow import run_assistant
    
    results = []
    
    for test in TEST_CASES:
        print(f"\n{'='*60}")
        print(f"Test {test['id']}: {test['type'].upper()}")
        print(f"Input: {test['input']}")
        print(f"{'='*60}")
        
        try:
            result = run_assistant(test['input'])
            
            print("\n📄 Final Output (truncated):")
            output = result.get('final_output', result.get('draft', 'No output'))
            print(output[:500] + "..." if len(output) > 500 else output)
            
            print("\n✅ Expected Behaviors:")
            for behavior in test['expected_behavior']:
                print(f"  • {behavior}")
            
            print("\n🔍 Verification:", "PASSED" if result.get('verification_passed') else "ISSUES FOUND")
            
            results.append({
                "test_id": test['id'],
                "type": test['type'],
                "completed": True,
                "verified": result.get('verification_passed', False)
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                "test_id": test['id'],
                "type": test['type'],
                "completed": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    
    completed = sum(1 for r in results if r['completed'])
    verified = sum(1 for r in results if r.get('verified', False))
    
    print(f"Total tests: {len(TEST_CASES)}")
    print(f"Completed: {completed}/{len(TEST_CASES)}")
    print(f"Verified: {verified}/{len(TEST_CASES)}")
    
    return results


if __name__ == "__main__":
    run_evaluation()