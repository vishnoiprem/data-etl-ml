"""
Helper utilities for document processing pipeline
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import base64
import re
import time
from functools import wraps
import inspect

logger = logging.getLogger(__name__)

class PipelineHelpers:
    """General helper utilities for the pipeline"""

    @staticmethod
    def generate_document_id(file_path: str, content: Optional[bytes] = None) -> str:
        """Generate unique document ID"""
        # Use SHA-256 hash of file path and/or content
        hash_input = file_path.encode('utf-8')
        if content:
            hash_input += content

        return hashlib.sha256(hash_input).hexdigest()

    @staticmethod
    def calculate_checksum(content: bytes, algorithm: str = 'sha256') -> str:
        """Calculate checksum for content"""
        if algorithm.lower() == 'sha256':
            return hashlib.sha256(content).hexdigest()
        elif algorithm.lower() == 'md5':
            return hashlib.md5(content).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    @staticmethod
    def infer_content_type(file_path: str) -> str:
        """Infer content type from file extension"""
        extension = Path(file_path).suffix.lower()

        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.bmp': 'image/bmp',
            '.gif': 'image/gif',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }

        return content_types.get(extension, 'application/octet-stream')

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def safe_json_serialize(obj: Any) -> Any:
        """Safely serialize object to JSON"""
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        elif isinstance(obj, (bytes,)):
            return base64.b64encode(obj).decode('utf-8')
        elif isinstance(obj, (set,)):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

    @staticmethod
    def create_timestamp() -> str:
        """Create ISO format timestamp"""
        return datetime.utcnow().isoformat() + 'Z'

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime:
        """Parse ISO format timestamp"""
        try:
            # Try parsing with timezone info
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            # Fallback for other formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y%m%d_%H%M%S']:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse timestamp: {timestamp_str}")

    @staticmethod
    def time_range_to_string(start_time: datetime, end_time: datetime) -> str:
        """Format time range as string"""
        duration = end_time - start_time
        return f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%Y-%m-%d %H:%M:%S')} ({duration})"

    @staticmethod
    def retry_with_backoff(max_retries: int = 3,
                          base_delay: float = 1.0,
                          max_delay: float = 60.0):
        """Decorator for retrying functions with exponential backoff"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt == max_retries - 1:
                            raise

                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (2 ** attempt), max_delay)

                        # Add jitter
                        jitter = delay * 0.1
                        delay += jitter * (2 * (time.time() % 1) - 1)

                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        time.sleep(delay)

                raise last_exception  # Should never reach here
            return wrapper
        return decorator

    @staticmethod
    def measure_execution_time(func):
        """Decorator to measure function execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            logger.info(
                f"Function {func.__name__} executed in {execution_time:.2f} seconds "
                f"({execution_time*1000:.0f} ms)"
            )

            # Add execution time to result if it's a dict
            if isinstance(result, dict):
                result['execution_time_seconds'] = execution_time

            return result
        return wrapper

    @staticmethod
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split list into chunks of specified size"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

    @staticmethod
    def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
        """Flatten a list of lists"""
        return [item for sublist in nested_list for item in sublist]

    @staticmethod
    def safe_get(dictionary: Dict, *keys, default: Any = None) -> Any:
        """Safely get nested dictionary value"""
        current = dictionary
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @staticmethod
    def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
        """Merge two dictionaries, with dict2 taking precedence"""
        result = dict1.copy()
        result.update(dict2)
        return result

    @staticmethod
    def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = PipelineHelpers.deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

class FileSystemHelpers:
    """File system related helper utilities"""

    @staticmethod
    def ensure_directory(directory_path: str) -> None:
        """Ensure directory exists, create if it doesn't"""
        Path(directory_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get file information"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat_info = path.stat()

        return {
            'file_name': path.name,
            'file_path': str(path.absolute()),
            'file_size': stat_info.st_size,
            'created_time': datetime.fromtimestamp(stat_info.st_ctime),
            'modified_time': datetime.fromtimestamp(stat_info.st_mtime),
            'accessed_time': datetime.fromtimestamp(stat_info.st_atime),
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'extension': path.suffix.lower(),
            'parent_dir': str(path.parent.absolute())
        }

    @staticmethod
    def find_files(directory: str,
                   pattern: str = "*",
                   recursive: bool = True) -> List[str]:
        """Find files matching pattern in directory"""
        path = Path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        # Filter to only files (not directories)
        files = [str(f.absolute()) for f in files if f.is_file()]

        return files

    @staticmethod
    def safe_read_file(file_path: str, mode: str = 'rb') -> Optional[bytes]:
        """Safely read file content"""
        try:
            with open(file_path, mode) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    @staticmethod
    def safe_write_file(file_path: str,
                       content: Union[str, bytes],
                       mode: str = 'wb') -> bool:
        """Safely write content to file"""
        try:
            # Ensure directory exists
            FileSystemHelpers.ensure_directory(os.path.dirname(file_path))

            with open(file_path, mode) as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False

    @staticmethod
    def get_directory_size(directory: str) -> Tuple[int, int]:
        """Get total size and file count in directory"""
        total_size = 0
        file_count = 0

        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                    file_count += 1
                except OSError:
                    continue

        return total_size, file_count

class ConfigHelpers:
    """Configuration related helper utilities"""

    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file"""
        import yaml

        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")

        return config or {}

    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str) -> bool:
        """Save configuration to file"""
        import yaml

        config_path = Path(config_path)

        try:
            FileSystemHelpers.ensure_directory(config_path.parent)

            with open(config_path, 'w') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False)
                elif config_path.suffix.lower() == '.json':
                    json.dump(config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config file format: {config_path.suffix}")

            return True
        except Exception as e:
            logger.error(f"Error saving config to {config_path}: {e}")
            return False

    @staticmethod
    def get_env_variable(key: str, default: Any = None) -> Any:
        """Get environment variable with fallback"""
        value = os.environ.get(key)
        if value is None:
            return default

        # Try to parse as JSON if it looks like JSON
        if value.startswith('{') or value.startswith('['):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Try to parse as boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        return value

class LoggingHelpers:
    """Logging related helper utilities"""

    @staticmethod
    def setup_logging(log_level: str = "INFO",
                     log_file: Optional[str] = None,
                     log_format: Optional[str] = None) -> None:
        """Setup logging configuration"""

        if log_format is None:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        level = getattr(logging, log_level.upper(), logging.INFO)

        # Configure root logger
        logging.basicConfig(
            level=level,
            format=log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Add file handler if log_file is specified
        if log_file:
            FileSystemHelpers.ensure_directory(os.path.dirname(log_file))

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(log_format))

            logging.getLogger().addHandler(file_handler)

        logger.info(f"Logging configured with level: {log_level}")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get logger with specified name"""
        return logging.getLogger(name)

    @staticmethod
    def log_execution_summary(operation: str,
                            start_time: datetime,
                            end_time: datetime,
                            metrics: Dict[str, Any]) -> None:
        """Log execution summary"""
        duration = end_time - start_time
        duration_str = str(duration).split('.')[0]  # Remove microseconds

        logger.info(f"Execution Summary - {operation}")
        logger.info(f"  Start Time: {start_time}")
        logger.info(f"  End Time: {end_time}")
        logger.info(f"  Duration: {duration_str}")

        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                logger.info(f"  {key}: {value:,}")
            else:
                logger.info(f"  {key}: {value}")

class PerformanceHelpers:
    """Performance monitoring and optimization helpers"""

    @staticmethod
    def monitor_memory_usage() -> Dict[str, float]:
        """Monitor current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent()
            }
        except ImportError:
            logger.warning("psutil not installed, memory monitoring disabled")
            return {}

    @staticmethod
    def monitor_cpu_usage() -> Dict[str, float]:
        """Monitor CPU usage"""
        try:
            import psutil
            return {
                'percent': psutil.cpu_percent(interval=0.1),
                'count': psutil.cpu_count(),
                'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except ImportError:
            logger.warning("psutil not installed, CPU monitoring disabled")
            return {}

    @staticmethod
    def estimate_processing_time(document_count: int,
                               avg_document_size_mb: float,
                               parallelism: int = 1) -> float:
        """Estimate total processing time"""
        # Very rough estimation - adjust based on your actual performance
        base_time_per_mb = 2.0  # seconds per MB (adjust based on your infrastructure)
        estimated_time = (document_count * avg_document_size_mb * base_time_per_mb) / parallelism

        return estimated_time

    @staticmethod
    def optimize_batch_size(avg_document_size_mb: float,
                          available_memory_mb: float,
                          memory_safety_factor: float = 0.7) -> int:
        """Calculate optimal batch size based on memory constraints"""
        # Estimate memory per document (adjust based on your processing)
        memory_per_document_mb = avg_document_size_mb * 3  # Rough estimate

        # Calculate safe batch size
        safe_memory = available_memory_mb * memory_safety_factor
        batch_size = int(safe_memory / memory_per_document_mb)

        # Ensure minimum and maximum bounds
        batch_size = max(1, min(batch_size, 100))

        return batch_size