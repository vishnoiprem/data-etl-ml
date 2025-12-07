# utils/model_selector.py
"""
Intelligent model selection for Azure Document Intelligence
Optimizes cost and accuracy based on document characteristics
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ModelType(Enum):
    READ = "prebuilt-read"  # $1.50/1K pages
    LAYOUT = "prebuilt-layout"  # $10/1K pages
    INVOICE = "prebuilt-invoice"  # $10/1K docs
    RECEIPT = "prebuilt-receipt"  # $10/1K docs
    ID = "prebuilt-idDocument"  # $10/1K docs


@dataclass
class ModelSelectionRule:
    """Rule for model selection"""
    model_type: ModelType
    conditions: List[callable]
    priority: int = 1
    cost_multiplier: float = 1.0


class ModelSelector:
    """Intelligently selects the best model for each document"""

    # Pre-compiled regex patterns
    INVOICE_PATTERNS = [
        r'invoice', r'bill', r'inv-', r'inv_\d+', r'\bINV\d+\b',
        r'tax\s*invoice', r'commercial\s*invoice', r'proforma'
    ]

    RECEIPT_PATTERNS = [
        r'receipt', r'sales\s*receipt', r'payment\s*receipt',
        r'cash\s*receipt', r'\bPOS\b', r'register\s*receipt'
    ]

    ID_PATTERNS = [
        r'passport', r'driver.?license', r'id.?card', r'national.?id',
        r'social.?security', r'visa', r'permit'
    ]

    # Cost comparison (relative to READ)
    MODEL_COSTS = {
        ModelType.READ: 1.0,  # Base cost
        ModelType.LAYOUT: 6.67,  # 6.67x more expensive
        ModelType.INVOICE: 6.67,
        ModelType.RECEIPT: 6.67,
        ModelType.ID: 6.67
    }

    @staticmethod
    def select_model(file_path: str,
                     user_preference: str = "auto",
                     content_sample: Optional[str] = None) -> str:
        """
        Select the most appropriate model based on document characteristics

        Args:
            file_path: Path to the document file
            user_preference: User's model preference ('auto', 'read', 'layout', etc.)
            content_sample: Optional text sample for content analysis

        Returns:
            Selected model ID
        """

        if user_preference != "auto":
            return ModelSelector._get_model_by_name(user_preference)

        # Analyze document characteristics
        file_extension = file_path.lower().split('.')[-1]
        file_name = file_path.lower().split('/')[-1]

        # Check file name for document type indicators
        if ModelSelector._is_invoice(file_name, content_sample):
            return ModelType.INVOICE.value

        if ModelSelector._is_receipt(file_name, content_sample):
            return ModelType.RECEIPT.value

        if ModelSelector._is_id_document(file_name, content_sample):
            return ModelType.ID.value

        # Check if document likely contains tables
        if content_sample and ModelSelector._contains_tables(content_sample):
            return ModelType.LAYOUT.value

        # For image files, check if they're likely scanned documents
        if file_extension in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
            # If it's an image but we don't have specific type, use READ
            return ModelType.READ.value

        # Default to LAYOUT for PDFs and DOCX (likely structured)
        if file_extension in ['pdf', 'docx']:
            return ModelType.LAYOUT.value

        # Fallback to READ for everything else
        return ModelType.READ.value

    @staticmethod
    def _get_model_by_name(name: str) -> str:
        """Convert model name string to ModelType value"""
        name = name.lower().replace('prebuilt-', '')

        mapping = {
            'read': ModelType.READ.value,
            'layout': ModelType.LAYOUT.value,
            'invoice': ModelType.INVOICE.value,
            'receipt': ModelType.RECEIPT.value,
            'id': ModelType.ID.value,
            'iddocument': ModelType.ID.value
        }

        return mapping.get(name, ModelType.LAYOUT.value)

    @staticmethod
    def _is_invoice(file_name: str, content: Optional[str]) -> bool:
        """Check if document appears to be an invoice"""

        # Check file name
        for pattern in ModelSelector.INVOICE_PATTERNS:
            if re.search(pattern, file_name, re.IGNORECASE):
                return True

        # Check content if available
        if content:
            content_lower = content.lower()
            for pattern in ModelSelector.INVOICE_PATTERNS:
                if re.search(pattern, content_lower):
                    return True

            # Check for common invoice fields
            invoice_indicators = [
                r'total\s*amount', r'invoice\s*date', r'invoice\s*number',
                r'customer\s*id', r'item\s*description', r'quantity',
                r'unit\s*price', r'subtotal', r'tax\s*rate'
            ]

            indicators_found = sum(
                1 for pattern in invoice_indicators
                if re.search(pattern, content_lower)
            )

            if indicators_found >= 3:
                return True

        return False

    @staticmethod
    def _is_receipt(file_name: str, content: Optional[str]) -> bool:
        """Check if document appears to be a receipt"""

        # Check file name
        for pattern in ModelSelector.RECEIPT_PATTERNS:
            if re.search(pattern, file_name, re.IGNORECASE):
                return True

        # Check content if available
        if content:
            content_lower = content.lower()
            for pattern in ModelSelector.RECEIPT_PATTERNS:
                if re.search(pattern, content_lower):
                    return True

            # Check for receipt-specific patterns
            receipt_indicators = [
                r'terminal\s*id', r'card\s*number', r'authorization\s*code',
                r'store\s*number', r'cashier\s*id', r'transaction\s*id',
                r'change\s*due', r'payment\s*method', r'vat\s*number'
            ]

            indicators_found = sum(
                1 for pattern in receipt_indicators
                if re.search(pattern, content_lower)
            )

            if indicators_found >= 2:
                return True

        return False

    @staticmethod
    def _is_id_document(file_name: str, content: Optional[str]) -> bool:
        """Check if document appears to be an ID document"""

        # Check file name
        for pattern in ModelSelector.ID_PATTERNS:
            if re.search(pattern, file_name, re.IGNORECASE):
                return True

        # Check content if available
        if content:
            content_lower = content.lower()
            for pattern in ModelSelector.ID_PATTERNS:
                if re.search(pattern, content_lower):
                    return True

        return False

    @staticmethod
    def _contains_tables(content: str) -> bool:
        """Heuristic check if content contains tabular data"""

        # Check for common table indicators
        lines = content.split('\n')

        # Count lines with multiple separators (commas, tabs, pipes)
        table_like_lines = 0
        for line in lines:
            # Check for CSV-like patterns
            if line.count(',') >= 3 and len(line.split(',')) >= 4:
                table_like_lines += 1

            # Check for tab-separated values
            elif line.count('\t') >= 2 and len(line.split('\t')) >= 3:
                table_like_lines += 1

            # Check for pipe-separated values
            elif line.count('|') >= 2 and len(line.split('|')) >= 3:
                table_like_lines += 1

        # If at least 3 lines look like table rows, assume it's a table
        if table_like_lines >= 3:
            return True

        # Check for column alignment patterns
        column_patterns = [
            r'\s{3,}.+\s{3,}.+\s{3,}.+',  # Multiple columns with spacing
            r'.+\s{2,}\d+\s{2,}.+',  # Numbers separated by spaces
        ]

        for pattern in column_patterns:
            matches = sum(1 for line in lines if re.match(pattern, line))
            if matches >= 3:
                return True

        return False

    @staticmethod
    def calculate_cost_savings(usage_data: Dict[str, int]) -> Dict[str, float]:
        """
        Calculate cost savings from intelligent model selection

        Args:
            usage_data: Dictionary of model usage counts

        Returns:
            Dictionary with cost analysis
        """

        # Calculate costs with current selection
        current_cost = sum(
            usage_data.get(model.value, 0) * ModelSelector.MODEL_COSTS[model]
            for model in ModelType
        )

        # Calculate cost if everything used LAYOUT (worst case)
        total_pages = sum(usage_data.values())
        worst_case_cost = total_pages * ModelSelector.MODEL_COSTS[ModelType.LAYOUT]

        # Calculate cost if everything used READ (best case for cost, worst for accuracy)
        best_case_cost = total_pages * ModelSelector.MODEL_COSTS[ModelType.READ]

        savings_vs_worst = worst_case_cost - current_cost
        savings_percentage = (savings_vs_worst / worst_case_cost * 100) if worst_case_cost > 0 else 0

        return {
            "current_cost": current_cost,
            "worst_case_cost": worst_case_cost,
            "best_case_cost": best_case_cost,
            "savings_amount": savings_vs_worst,
            "savings_percentage": savings_percentage,
            "total_pages": total_pages,
            "usage_by_model": usage_data
        }