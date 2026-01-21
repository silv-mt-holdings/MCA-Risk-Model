"""
MCA Risk Model CLI
==================
Command-line interface for MCA risk scoring.

Usage:
    python cli.py score --fico 680 --industry restaurant
    python cli.py analyze statement.pdf --output metrics.json
"""

import argparse
import json
import sys
from pathlib import Path


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='MCA Risk Model - Bank statement analysis and risk scoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Score command
    score_parser = subparsers.add_parser('score', help='Score a deal')
    score_parser.add_argument('statement', nargs='?', help='Bank statement PDF path')
    score_parser.add_argument('--fico', type=int, default=0, help='FICO credit score')
    score_parser.add_argument('--industry', default='', help='Industry type')
    score_parser.add_argument('--positions', type=int, default=0, help='Existing MCA positions')
    score_parser.add_argument('--amount', type=float, default=0, help='Funding amount requested')
    score_parser.add_argument('--output', '-o', help='Output file path (JSON)')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze bank statement only')
    analyze_parser.add_argument('statement', help='Bank statement PDF path')
    analyze_parser.add_argument('--output', '-o', help='Output file path (JSON)')

    # Config command
    config_parser = subparsers.add_parser('config', help='Show or update configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current config')
    config_parser.add_argument('--weights', help='Path to weights JSON')
    config_parser.add_argument('--grades', help='Path to grades JSON')

    return parser.parse_args()


def cmd_score(args):
    """Execute score command"""
    print("MCA Risk Score")
    print("=" * 40)

    # Import scoring module
    try:
        from scoring import RBFScoringModel
    except ImportError:
        print("Error: Could not import scoring module.")
        print("Make sure the package is installed: pip install -e .")
        return 1

    # Create scorecard
    scorecard = RBFScoringModel()

    # Set metrics from arguments
    if args.fico:
        scorecard.set_credit_metrics(fico_score=args.fico)

    if args.industry:
        scorecard.set_industry(args.industry)

    if args.positions or args.amount:
        scorecard.set_deal_metrics(
            position_count=args.positions,
            funding_amount=args.amount,
        )

    # Parse statement if provided
    if args.statement:
        print(f"\nParsing: {args.statement}")
        # TODO: Implement statement parsing
        print("(Statement parsing not yet implemented)")

    # Calculate score
    result = scorecard.calculate()

    # Print results
    print(f"\n{result.summary()}")

    # Save output if requested
    if args.output:
        output = {
            'score': result.score,
            'grade': result.letter_grade,
            'risk_flags': result.risk_flags,
            'recommendation': result.recommendation,
        }
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to: {args.output}")

    return 0


def cmd_analyze(args):
    """Execute analyze command"""
    print("Bank Statement Analysis")
    print("=" * 40)
    print(f"\nAnalyzing: {args.statement}")
    print("\n(Analysis module not yet implemented)")
    return 0


def cmd_config(args):
    """Execute config command"""
    if args.show:
        print("Current Configuration")
        print("=" * 40)

        # Load and display configs
        config_dir = Path(__file__).parent / 'data'

        weights_path = config_dir / 'scoring_weights.json'
        if weights_path.exists():
            with open(weights_path) as f:
                weights = json.load(f)
            print("\nScoring Weights:")
            for cat, info in weights.get('weights', {}).items():
                print(f"  {cat}: {info['weight']*100:.0f}%")

        grades_path = config_dir / 'letter_grade_thresholds.json'
        if grades_path.exists():
            with open(grades_path) as f:
                grades = json.load(f)
            print("\nGrade Thresholds:")
            for grade, info in grades.get('grades', {}).items():
                print(f"  {grade}: {info['min_score']}-{info['max_score']} ({info['risk_level']})")

    return 0


def main():
    """Main entry point"""
    args = parse_args()

    if args.command == 'score':
        return cmd_score(args)
    elif args.command == 'analyze':
        return cmd_analyze(args)
    elif args.command == 'config':
        return cmd_config(args)
    else:
        print("MCA Risk Model v1.0")
        print("=" * 40)
        print("\nUsage:")
        print("  python cli.py score --fico 680 --industry restaurant")
        print("  python cli.py analyze statement.pdf")
        print("  python cli.py config --show")
        print("\nUse --help for more options")
        return 0


if __name__ == '__main__':
    sys.exit(main())
