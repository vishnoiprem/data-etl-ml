"""
Validation utilities for document processing pipeline
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


class DocumentValidator:
    """Validates documents and processing results"""

    # Common file extensions for validation
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.txt', '.rtf',
        '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif'
    }

    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    PHONE_PATTERN = re.compile(r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}')

    def __init__(self):
        self.validation_rules = self._load_default_rules()

    def _load_default_rules(self) -> Dict[str, Any]:
        """Load default validation rules"""
        return {
            'file_size_limit': self.MAX_FILE_SIZE,
            'supported_extensions': self.SUPPORTED_EXTENSIONS,
            'min_confidence_score': 0.5,
            'max_pages': 1000,
            'max_word_count': 100000,
            'required_fields': ['document_id', 'file_name', 'file_path'],
            'date_formats': ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d']
        }

    def validate_file(self,
                      file_path: str,
                      file_size: int,
                      content_type: Optional[str] = None) -> ValidationResult:
        """Validate file before processing"""
        result = ValidationResult(is_valid=True)

        # Check file size
        if file_size > self.validation_rules['file_size_limit']:
            result.is_valid = False
            result.errors.append(
                f"File size {file_size} bytes exceeds limit of {self.validation_rules['file_size_limit']} bytes"
            )

        # Check file extension
        import os
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.validation_rules['supported_extensions']:
            result.is_valid = False
            result.errors.append(f"Unsupported file extension: {file_ext}")

        # Check if file appears to be corrupted or empty
        if file_size == 0:
            result.is_valid = False
            result.errors.append("File is empty (0 bytes)")

        return result

    def validate_extraction(self, extraction_result: Dict[str, Any]) -> ValidationResult:
        """Validate document extraction results"""
        result = ValidationResult(is_valid=True)

        # Check required fields
        required_fields = ['content', 'page_count', 'confidence_score']
        for field in required_fields:
            if field not in extraction_result:
                result.is_valid = False
                result.errors.append(f"Missing required field: {field}")

        if not result.is_valid:
            return result

        # Validate confidence score
        confidence = extraction_result.get('confidence_score', 0)
        if not (0 <= confidence <= 1):
            result.is_valid = False
            result.errors.append(f"Invalid confidence score: {confidence}")
        elif confidence < self.validation_rules['min_confidence_score']:
            result.warnings.append(f"Low confidence score: {confidence}")

        # Validate page count
        page_count = extraction_result.get('page_count', 0)
        if page_count < 0:
            result.is_valid = False
            result.errors.append(f"Invalid page count: {page_count}")
        elif page_count > self.validation_rules['max_pages']:
            result.warnings.append(f"High page count: {page_count}")

        # Validate content
        content = extraction_result.get('content', '')
        if not content or not content.strip():
            result.warnings.append("Extracted content is empty or very short")
        else:
            # Check content length
            word_count = len(content.split())
            if word_count > self.validation_rules['max_word_count']:
                result.warnings.append(f"High word count: {word_count}")

            # Check for common issues
            if '�' in content or '??' in content:
                result.warnings.append("Content contains replacement characters indicating encoding issues")

        # Validate structured data if present
        if 'tables' in extraction_result:
            tables = extraction_result['tables']
            if not isinstance(tables, list):
                result.warnings.append("Tables field is not a list")
            else:
                for i, table in enumerate(tables):
                    if not isinstance(table, dict):
                        result.warnings.append(f"Table {i} is not a dictionary")
                    elif 'cells' not in table:
                        result.warnings.append(f"Table {i} missing cells")

        return result

    def validate_schema(self,
                        data: Dict[str, Any],
                        schema: Dict[str, Any]) -> ValidationResult:
        """Validate data against a JSON schema"""
        result = ValidationResult(is_valid=True)

        # Simple schema validation (for production, use a proper JSON schema validator)
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})

        # Check required fields
        for field in required_fields:
            if field not in data:
                result.is_valid = False
                result.errors.append(f"Missing required field: {field}")

        # Check field types
        for field_name, field_value in data.items():
            if field_name in properties:
                field_schema = properties[field_name]
                expected_type = field_schema.get('type')

                if expected_type:
                    type_valid = self._validate_type(field_value, expected_type)
                    if not type_valid:
                        result.is_valid = False
                        result.errors.append(
                            f"Field '{field_name}' has wrong type. "
                            f"Expected {expected_type}, got {type(field_value).__name__}"
                        )

                # Check constraints if specified
                constraints = field_schema.get('constraints', {})
                if 'min' in constraints and field_value < constraints['min']:
                    result.is_valid = False
                    result.errors.append(
                        f"Field '{field_name}' value {field_value} "
                        f"is less than minimum {constraints['min']}"
                    )

                if 'max' in constraints and field_value > constraints['max']:
                    result.is_valid = False
                    result.errors.append(
                        f"Field '{field_name}' value {field_value} "
                        f"is greater than maximum {constraints['max']}"
                    )

                if 'pattern' in constraints:
                    pattern = constraints['pattern']
                    if not re.match(pattern, str(field_value)):
                        result.is_valid = False
                        result.errors.append(
                            f"Field '{field_name}' value does not match pattern: {pattern}"
                        )

        return result

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type"""
        type_mapping = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }

        if expected_type not in type_mapping:
            return True  # Unknown type, skip validation

        expected = type_mapping[expected_type]
        if isinstance(expected, tuple):
            return any(isinstance(value, t) for t in expected)
        return isinstance(value, expected)

    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        if not email:
            return False
        return bool(self.EMAIL_PATTERN.match(email.strip()))

    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        return bool(self.PHONE_PATTERN.match(phone.strip()))

    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False
        return bool(self.URL_PATTERN.match(url.strip()))

    def validate_date(self, date_str: str, date_formats: List[str] = None) -> Tuple[bool, Optional[datetime]]:
        """Validate date string"""
        if not date_str:
            return False, None

        if date_formats is None:
            date_formats = self.validation_rules['date_formats']

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return True, dt
            except ValueError:
                continue

        return False, None

    def validate_numeric_range(self,
                               value: Any,
                               min_val: Optional[float] = None,
                               max_val: Optional[float] = None) -> bool:
        """Validate numeric value is within range"""
        try:
            num = float(value)
        except (ValueError, TypeError):
            return False

        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False

        return True

    def validate_json(self, json_str: str) -> Tuple[bool, Optional[Dict]]:
        """Validate JSON string"""
        try:
            data = json.loads(json_str)
            return True, data
        except json.JSONDecodeError as e:
            return False, None

    def validate_checksum(self,
                          content: bytes,
                          expected_checksum: str,
                          algorithm: str = 'sha256') -> bool:
        """Validate content checksum"""
        import hashlib

        if algorithm.lower() == 'sha256':
            calculated = hashlib.sha256(content).hexdigest()
        elif algorithm.lower() == 'md5':
            calculated = hashlib.md5(content).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        return calculated == expected_checksum

    def sanitize_text(self, text: str) -> str:
        """Sanitize text by removing problematic characters"""
        if not text:
            return ""

        # Remove null characters
        text = text.replace('\x00', '')

        # Replace other problematic characters
        replacements = {
            '\u2028': '\n',  # Line separator
            '\u2029': '\n\n',  # Paragraph separator
            '\uFEFF': '',  # Zero-width no-break space
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        return text

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        Detect Personally Identifiable Information in text

        Note: This is a basic implementation. For production, use
        Azure PII detection service or similar enterprise solution.
        """
        pii_found = {
            'emails': [],
            'phones': [],
            'urls': [],
            'potential_ssn': []
        }

        if not text:
            return pii_found

        # Find emails
        pii_found['emails'] = self.EMAIL_PATTERN.findall(text)

        # Find phone numbers
        pii_found['phones'] = self.PHONE_PATTERN.findall(text)

        # Find URLs
        pii_found['urls'] = self.URL_PATTERN.findall(text)

        # Find potential SSNs (US Social Security Numbers)
        ssn_pattern = re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b')
        pii_found['potential_ssn'] = ssn_pattern.findall(text)

        return pii_found

    def create_validation_report(self,
                                 validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Create a summary report from multiple validation results"""
        total_valid = sum(1 for r in validation_results if r.is_valid)
        total_errors = sum(len(r.errors) for r in validation_results)
        total_warnings = sum(len(r.warnings) for r in validation_results)

        # Group errors by type
        error_types = {}
        for result in validation_results:
            for error in result.errors:
                # Extract error type (first word or key phrase)
                error_type = error.split(':')[0] if ':' in error else error.split()[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            'total_validations': len(validation_results),
            'total_valid': total_valid,
            'total_invalid': len(validation_results) - total_valid,
            'success_rate': total_valid / len(validation_results) if validation_results else 0,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'error_types': error_types,
            'has_critical_errors': any(not r.is_valid for r in validation_results)
        }