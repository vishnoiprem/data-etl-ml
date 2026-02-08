# src/monitoring/quality_checks.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import json
import os
from datetime import datetime


class DataQualityChecker:
    """Perform data quality checks"""

    def __init__(self):
        self.checks = {
            'completeness': self.check_completeness,
            'accuracy': self.check_accuracy,
            'consistency': self.check_consistency,
            'validity': self.check_validity,
            'uniqueness': self.check_uniqueness
        }

    def run_all_checks(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Run all quality checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'overall_score': 0.0
        }

        for source_name, df in data.items():
            source_results = {}

            for check_name, check_func in self.checks.items():
                check_result = check_func(df)
                source_results[check_name] = check_result

            source_score = self._calculate_source_score(source_results)
            source_results['score'] = source_score

            results['sources'][source_name] = source_results

        results['overall_score'] = self._calculate_overall_score(results['sources'])

        return results

    def check_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for missing values"""
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()

        critical_columns = ['gl_account', 'transaction_date', 'amount_local']
        critical_missing = 0
        critical_total = 0

        for col in critical_columns:
            if col in df.columns:
                critical_total += len(df)
                critical_missing += df[col].isnull().sum()

        return {
            'total_cells': total_cells,
            'missing_cells': missing_cells,
            'completeness_rate': 1 - (missing_cells / total_cells) if total_cells > 0 else 0,
            'critical_missing': critical_missing,
            'critical_completeness': 1 - (critical_missing / critical_total) if critical_total > 0 else 0
        }

    def check_accuracy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data accuracy"""
        results = {
            'negative_amounts': 0,
            'zero_amounts': 0,
            'unrealistic_values': 0
        }

        if 'amount_local' in df.columns:
            results['negative_amounts'] = (df['amount_local'] < 0).sum()
            results['zero_amounts'] = (df['amount_local'] == 0).sum()

            if df['amount_local'].count() > 0:
                mean = df['amount_local'].mean()
                std = df['amount_local'].std()
                if not pd.isna(std) and std > 0:
                    z_scores = np.abs((df['amount_local'] - mean) / std)
                    results['unrealistic_values'] = (z_scores > 3).sum()

        return results

    def check_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data consistency"""
        results = {
            'date_range_issues': 0,
            'currency_mismatches': 0
        }

        if 'transaction_date' in df.columns:
            future_dates = (df['transaction_date'] > datetime.now()).sum()
            too_old = (df['transaction_date'] < datetime(2000, 1, 1)).sum()
            results['date_range_issues'] = future_dates + too_old

        if 'country' in df.columns and 'currency_code' in df.columns:
            currency_map = {'TH': 'THB', 'VN': 'VND', 'ID': 'IDR'}
            mismatches = 0
            for country, expected_currency in currency_map.items():
                country_mask = df['country'] == country
                if country_mask.any():
                    currency_mismatch = (df.loc[country_mask, 'currency_code'] != expected_currency).sum()
                    mismatches += currency_mismatch
            results['currency_mismatches'] = mismatches

        return results

    def check_validity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data validity"""
        results = {
            'invalid_accounts': 0,
            'invalid_countries': 0
        }

        if 'gl_account' in df.columns:
            valid_accounts = ['401001', '401002', '401003', '501001', '501002', '501003',
                              '601001', '601002', '601003', '101001', '101002', '201001', '201002']
            results['invalid_accounts'] = (~df['gl_account'].isin(valid_accounts)).sum()

        if 'country' in df.columns:
            valid_countries = ['TH', 'VN', 'ID']
            results['invalid_countries'] = (~df['country'].isin(valid_countries)).sum()

        return results

    def check_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for duplicates"""
        results = {
            'total_records': len(df),
            'duplicate_records': 0
        }

        duplicate_fields = ['transaction_id', 'gl_account', 'amount_local', 'transaction_date']
        available_fields = [col for col in duplicate_fields if col in df.columns]

        if available_fields:
            results['duplicate_records'] = df.duplicated(subset=available_fields, keep=False).sum()

        return results

    def _calculate_source_score(self, source_results: Dict[str, Any]) -> float:
        """Calculate overall quality score for a source"""
        weights = {
            'completeness': 0.3,
            'accuracy': 0.25,
            'consistency': 0.2,
            'validity': 0.15,
            'uniqueness': 0.1
        }

        score = 0.0

        # Completeness score
        if 'completeness' in source_results:
            comp = source_results['completeness']
            completeness_score = comp.get('critical_completeness', 0.8) * 0.7 + comp.get('completeness_rate', 0.9) * 0.3
            score += completeness_score * weights['completeness']

        # Accuracy score (penalize issues)
        if 'accuracy' in source_results:
            acc = source_results['accuracy']
            total_issues = acc.get('negative_amounts', 0) + acc.get('unrealistic_values', 0)
            total_records = source_results.get('uniqueness', {}).get('total_records', 1000)
            accuracy_score = max(0, 1 - (total_issues / max(total_records, 1)))
            score += accuracy_score * weights['accuracy']

        # Consistency score
        if 'consistency' in source_results:
            cons = source_results['consistency']
            total_issues = cons.get('date_range_issues', 0) + cons.get('currency_mismatches', 0)
            total_records = source_results.get('uniqueness', {}).get('total_records', 1000)
            consistency_score = max(0, 1 - (total_issues / max(total_records, 1)))
            score += consistency_score * weights['consistency']

        # Validity score
        if 'validity' in source_results:
            val = source_results['validity']
            total_invalid = val.get('invalid_accounts', 0) + val.get('invalid_countries', 0)
            total_records = source_results.get('uniqueness', {}).get('total_records', 1000)
            validity_score = max(0, 1 - (total_invalid / max(total_records, 1)))
            score += validity_score * weights['validity']

        # Uniqueness score
        if 'uniqueness' in source_results:
            uni = source_results['uniqueness']
            duplicate_ratio = uni.get('duplicate_records', 0) / max(uni.get('total_records', 1), 1)
            uniqueness_score = max(0, 1 - duplicate_ratio)
            score += uniqueness_score * weights['uniqueness']

        return round(score, 3)

    def _calculate_overall_score(self, sources: Dict[str, Any]) -> float:
        """Calculate overall quality score across all sources"""
        if not sources:
            return 0.0

        total_score = sum(source_data.get('score', 0) for source_data in sources.values())
        return round(total_score / len(sources), 3)

    def generate_report(self, results: Dict[str, Any], output_path: str = "reports/quality_report.json"):
        """Generate quality report"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Quality report saved to {output_path}")

        # Print summary to console
        print("\n" + "=" * 60)
        print("DATA QUALITY REPORT")
        print("=" * 60)
        print(f"Overall Quality Score: {results.get('overall_score', 0):.1%}")
        print(f"Sources analyzed: {len(results.get('sources', {}))}")

        for source_name, source_results in results.get('sources', {}).items():
            print(f"\n{source_name}:")
            print(f"  Score: {source_results.get('score', 0):.1%}")
            for check_name, check_result in source_results.items():
                if check_name != 'score':
                    print(f"  {check_name}: {check_result}")