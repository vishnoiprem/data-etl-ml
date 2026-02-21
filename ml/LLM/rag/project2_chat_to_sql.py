"""
================================================================================
PROJECT 2: CHAT-TO-SQL SYSTEM
================================================================================
Letting business users query data without writing SQL

This prototype demonstrates the complete pipeline:
1. Natural language query parsing
2. Semantic layer mapping (business terms → database fields)
3. SQL generation with LLM
4. Guardrails and validation
5. Query execution with security
6. Result formatting

Tech Stack:
- OpenAI GPT-4 (query generation)
- SQLGlot (SQL parsing & validation)
- Pydantic (schema validation)
- PostgreSQL/Snowflake (database)
================================================================================
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class SQLConfig:
    """Configuration for the Chat-to-SQL system"""
    # LLM settings
    llm_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.0  # Zero for deterministic SQL
    
    # Query limits
    max_rows: int = 10000
    query_timeout_seconds: int = 30
    max_joins: int = 5
    max_subqueries: int = 3
    
    # Security
    enable_row_level_security: bool = True
    blocked_operations: List[str] = field(default_factory=lambda: [
        "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", 
        "ALTER", "CREATE", "GRANT", "REVOKE"
    ])


# ============================================================================
# DATA MODELS
# ============================================================================

class QueryIntent(Enum):
    """Types of queries we support"""
    AGGREGATION = "aggregation"  # COUNT, SUM, AVG, etc.
    LISTING = "listing"          # SELECT * with filters
    COMPARISON = "comparison"    # Compare metrics across dimensions
    TREND = "trend"              # Time-series analysis
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Parsed user intent from natural language"""
    intent_type: QueryIntent
    metrics: List[str]           # What to measure
    dimensions: List[str]        # How to group
    filters: Dict[str, Any]      # Where conditions
    time_range: Optional[Dict]   # Date filters
    limit: Optional[int]
    confidence: float


@dataclass
class SemanticMapping:
    """Maps business term to SQL expression"""
    business_term: str
    sql_expression: str
    description: str
    data_type: str
    example_values: List[str] = field(default_factory=list)


@dataclass 
class TableSchema:
    """Database table schema for validation"""
    name: str
    columns: Dict[str, str]  # column_name -> data_type
    primary_key: str
    foreign_keys: Dict[str, str] = field(default_factory=dict)


@dataclass
class GeneratedQuery:
    """Generated SQL query with metadata"""
    sql: str
    explanation: str
    tables_used: List[str]
    estimated_complexity: str  # low, medium, high
    warnings: List[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Result from query execution"""
    data: List[Dict]
    columns: List[str]
    row_count: int
    execution_time_ms: int
    query_id: str
    cached: bool = False


@dataclass
class ChatToSQLResponse:
    """Complete response from the system"""
    natural_query: str
    parsed_intent: ParsedIntent
    generated_sql: GeneratedQuery
    result: Optional[QueryResult]
    error: Optional[str] = None


# ============================================================================
# SEMANTIC LAYER
# ============================================================================

class SemanticLayer:
    """
    Maps business vocabulary to database schema.
    This is THE key innovation that makes Chat-to-SQL work reliably.
    """
    
    def __init__(self):
        self.mappings: Dict[str, SemanticMapping] = {}
        self.synonyms: Dict[str, str] = {}
        self._load_default_mappings()
    
    def _load_default_mappings(self):
        """Load business term mappings"""
        
        # Define mappings
        mappings = [
            # Customer metrics
            SemanticMapping(
                business_term="active customers",
                sql_expression="COUNT(DISTINCT customer_id) FILTER (WHERE status = 'active' AND type = 'customer')",
                description="Customers with active status",
                data_type="integer",
                example_values=["12847", "8500"]
            ),
            SemanticMapping(
                business_term="total customers",
                sql_expression="COUNT(DISTINCT customer_id)",
                description="All customers regardless of status",
                data_type="integer"
            ),
            SemanticMapping(
                business_term="new customers",
                sql_expression="COUNT(DISTINCT customer_id) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days')",
                description="Customers created in last 30 days",
                data_type="integer"
            ),
            SemanticMapping(
                business_term="churned customers",
                sql_expression="COUNT(DISTINCT customer_id) FILTER (WHERE status = 'churned')",
                description="Customers who have churned",
                data_type="integer"
            ),
            
            # Revenue metrics
            SemanticMapping(
                business_term="revenue",
                sql_expression="SUM(invoice_amount) FILTER (WHERE paid = true)",
                description="Total paid revenue",
                data_type="decimal",
                example_values=["1500000.00", "2300000.50"]
            ),
            SemanticMapping(
                business_term="average order value",
                sql_expression="AVG(order_total)",
                description="Average value per order",
                data_type="decimal"
            ),
            SemanticMapping(
                business_term="mrr",
                sql_expression="SUM(monthly_recurring_revenue)",
                description="Monthly Recurring Revenue",
                data_type="decimal"
            ),
            
            # Geographic dimensions
            SemanticMapping(
                business_term="northeast",
                sql_expression="region IN ('NY', 'NJ', 'CT', 'MA', 'PA', 'NH', 'VT', 'ME', 'RI')",
                description="Northeastern US states",
                data_type="filter"
            ),
            SemanticMapping(
                business_term="southeast",
                sql_expression="region IN ('FL', 'GA', 'NC', 'SC', 'VA', 'TN', 'AL', 'MS', 'LA')",
                description="Southeastern US states",
                data_type="filter"
            ),
            SemanticMapping(
                business_term="west coast",
                sql_expression="region IN ('CA', 'OR', 'WA')",
                description="West Coast US states",
                data_type="filter"
            ),
            
            # Time dimensions
            SemanticMapping(
                business_term="this month",
                sql_expression="date_trunc('month', CURRENT_DATE)",
                description="Current calendar month",
                data_type="date_filter"
            ),
            SemanticMapping(
                business_term="last quarter",
                sql_expression="date_trunc('quarter', CURRENT_DATE - INTERVAL '3 months')",
                description="Previous calendar quarter",
                data_type="date_filter"
            ),
            SemanticMapping(
                business_term="ytd",
                sql_expression="created_at >= date_trunc('year', CURRENT_DATE)",
                description="Year to date",
                data_type="date_filter"
            ),
            
            # Contract types
            SemanticMapping(
                business_term="renewals",
                sql_expression="contract_type = 'renewal'",
                description="Renewal contracts",
                data_type="filter"
            ),
            SemanticMapping(
                business_term="new business",
                sql_expression="contract_type = 'new'",
                description="New business contracts",
                data_type="filter"
            ),
            
            # Product categories
            SemanticMapping(
                business_term="enterprise customers",
                sql_expression="customer_tier = 'enterprise'",
                description="Enterprise tier customers",
                data_type="filter"
            ),
            SemanticMapping(
                business_term="smb customers",
                sql_expression="customer_tier IN ('small', 'medium')",
                description="Small and medium business customers",
                data_type="filter"
            ),
        ]
        
        for mapping in mappings:
            self.mappings[mapping.business_term.lower()] = mapping
        
        # Define synonyms
        self.synonyms = {
            "clients": "customers",
            "users": "customers",
            "accounts": "customers",
            "sales": "revenue",
            "income": "revenue",
            "bookings": "revenue",
            "aov": "average order value",
            "east coast": "northeast",
            "this year": "ytd",
            "year to date": "ytd",
        }
    
    def resolve_term(self, term: str) -> Optional[SemanticMapping]:
        """Resolve a business term to its SQL mapping"""
        term_lower = term.lower().strip()
        
        # Check direct mapping
        if term_lower in self.mappings:
            return self.mappings[term_lower]
        
        # Check synonyms
        if term_lower in self.synonyms:
            canonical = self.synonyms[term_lower]
            return self.mappings.get(canonical)
        
        # Fuzzy matching (simple contains check)
        for key, mapping in self.mappings.items():
            if term_lower in key or key in term_lower:
                return mapping
        
        return None
    
    def get_all_terms(self) -> List[str]:
        """Get all available business terms"""
        return list(self.mappings.keys()) + list(self.synonyms.keys())
    
    def to_prompt_context(self) -> str:
        """Generate context for LLM prompt"""
        lines = ["Available business terms and their meanings:\n"]
        
        for term, mapping in self.mappings.items():
            lines.append(f"- '{term}': {mapping.description}")
            lines.append(f"  SQL: {mapping.sql_expression}")
        
        return "\n".join(lines)


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

class SchemaManager:
    """
    Manages database schema for validation.
    Only allows queries against known tables and columns.
    """
    
    def __init__(self):
        self.tables: Dict[str, TableSchema] = {}
        self._load_schema()
    
    def _load_schema(self):
        """Load database schema (in production: read from database)"""
        
        self.tables = {
            "customers": TableSchema(
                name="customers",
                columns={
                    "customer_id": "uuid",
                    "name": "varchar",
                    "email": "varchar",
                    "status": "varchar",  # active, inactive, churned
                    "type": "varchar",    # customer, prospect
                    "customer_tier": "varchar",  # enterprise, small, medium
                    "region": "varchar",
                    "created_at": "timestamp",
                    "updated_at": "timestamp"
                },
                primary_key="customer_id"
            ),
            "orders": TableSchema(
                name="orders",
                columns={
                    "order_id": "uuid",
                    "customer_id": "uuid",
                    "order_total": "decimal",
                    "status": "varchar",
                    "created_at": "timestamp"
                },
                primary_key="order_id",
                foreign_keys={"customer_id": "customers.customer_id"}
            ),
            "invoices": TableSchema(
                name="invoices",
                columns={
                    "invoice_id": "uuid",
                    "customer_id": "uuid",
                    "invoice_amount": "decimal",
                    "paid": "boolean",
                    "due_date": "date",
                    "paid_date": "date"
                },
                primary_key="invoice_id",
                foreign_keys={"customer_id": "customers.customer_id"}
            ),
            "contracts": TableSchema(
                name="contracts",
                columns={
                    "contract_id": "uuid",
                    "customer_id": "uuid",
                    "contract_type": "varchar",  # new, renewal
                    "monthly_recurring_revenue": "decimal",
                    "start_date": "date",
                    "end_date": "date"
                },
                primary_key="contract_id",
                foreign_keys={"customer_id": "customers.customer_id"}
            )
        }
    
    def validate_table(self, table_name: str) -> bool:
        """Check if table exists in schema"""
        return table_name.lower() in self.tables
    
    def validate_column(self, table_name: str, column_name: str) -> bool:
        """Check if column exists in table"""
        table = self.tables.get(table_name.lower())
        if not table:
            return False
        return column_name.lower() in table.columns
    
    def get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        """Get schema for a table"""
        return self.tables.get(table_name.lower())
    
    def to_prompt_context(self) -> str:
        """Generate schema context for LLM prompt"""
        lines = ["Database Schema:\n"]
        
        for name, table in self.tables.items():
            lines.append(f"\nTable: {name}")
            lines.append("Columns:")
            for col, dtype in table.columns.items():
                lines.append(f"  - {col}: {dtype}")
        
        return "\n".join(lines)


# ============================================================================
# INTENT PARSER
# ============================================================================

class IntentParser:
    """
    Parses natural language queries into structured intents.
    Uses LLM with strict output format.
    """
    
    def __init__(self, config: SQLConfig, semantic_layer: SemanticLayer):
        self.config = config
        self.semantic_layer = semantic_layer
        
        self.system_prompt = """You are a query intent parser. Given a natural language question about business data, extract the structured intent.

Output JSON with this exact structure:
{
    "intent_type": "aggregation|listing|comparison|trend",
    "metrics": ["list of metrics to calculate"],
    "dimensions": ["list of dimensions to group by"],
    "filters": {"field": "value"},
    "time_range": {"start": "date", "end": "date"} or null,
    "limit": number or null
}

Be precise. Only include fields mentioned in the query."""

    def parse(self, query: str) -> ParsedIntent:
        """Parse natural language query into structured intent"""
        
        # In production: call LLM
        """
        from openai import OpenAI
        client = OpenAI()
        
        response = client.chat.completions.create(
            model=self.config.llm_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Parse this query: {query}"}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content)
        """
        
        # Simplified parsing for demo
        parsed = self._simple_parse(query)
        
        return ParsedIntent(
            intent_type=QueryIntent(parsed.get("intent_type", "aggregation")),
            metrics=parsed.get("metrics", []),
            dimensions=parsed.get("dimensions", []),
            filters=parsed.get("filters", {}),
            time_range=parsed.get("time_range"),
            limit=parsed.get("limit"),
            confidence=0.9
        )
    
    def _simple_parse(self, query: str) -> Dict:
        """Simple rule-based parsing for demo"""
        query_lower = query.lower()
        
        result = {
            "intent_type": "aggregation",
            "metrics": [],
            "dimensions": [],
            "filters": {},
            "time_range": None,
            "limit": None
        }
        
        # Detect metrics
        if "how many" in query_lower or "count" in query_lower:
            result["metrics"].append("count")
        if "revenue" in query_lower or "sales" in query_lower:
            result["metrics"].append("revenue")
        if "average" in query_lower:
            result["metrics"].append("average")
        
        # Detect filters
        if "active" in query_lower:
            result["filters"]["status"] = "active"
        if "northeast" in query_lower:
            result["filters"]["region"] = "northeast"
        if "enterprise" in query_lower:
            result["filters"]["tier"] = "enterprise"
        
        # Detect intent type
        if "list" in query_lower or "show me" in query_lower:
            result["intent_type"] = "listing"
        if "compare" in query_lower or "vs" in query_lower:
            result["intent_type"] = "comparison"
        if "trend" in query_lower or "over time" in query_lower:
            result["intent_type"] = "trend"
        
        return result


# ============================================================================
# SQL GENERATOR
# ============================================================================

class SQLGenerator:
    """
    Generates SQL from parsed intent using LLM.
    """
    
    def __init__(
        self, 
        config: SQLConfig, 
        semantic_layer: SemanticLayer,
        schema_manager: SchemaManager
    ):
        self.config = config
        self.semantic_layer = semantic_layer
        self.schema_manager = schema_manager
        
        self.system_prompt = """You are a SQL query generator. Generate PostgreSQL queries based on the user's intent and the provided schema.

RULES:
1. ONLY use tables and columns from the provided schema
2. Use the semantic mappings for business terms
3. NEVER use DROP, DELETE, TRUNCATE, UPDATE, INSERT, ALTER, CREATE
4. Always include appropriate WHERE clauses
5. Use CTEs for complex queries
6. Add LIMIT clause for safety
7. Use meaningful aliases

Output JSON:
{
    "sql": "the SQL query",
    "explanation": "plain English explanation of what the query does",
    "tables_used": ["list of tables"],
    "complexity": "low|medium|high"
}"""

    def generate(self, intent: ParsedIntent, original_query: str) -> GeneratedQuery:
        """Generate SQL from parsed intent"""
        
        # Build context for LLM
        context = f"""
{self.schema_manager.to_prompt_context()}

{self.semantic_layer.to_prompt_context()}

User's original question: {original_query}

Parsed intent:
- Type: {intent.intent_type.value}
- Metrics: {intent.metrics}
- Dimensions: {intent.dimensions}
- Filters: {intent.filters}
- Time range: {intent.time_range}
- Limit: {intent.limit}
"""
        
        # In production: call LLM
        """
        from openai import OpenAI
        client = OpenAI()
        
        response = client.chat.completions.create(
            model=self.config.llm_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        """
        
        # Demo SQL generation
        result = self._generate_demo_sql(intent)
        
        return GeneratedQuery(
            sql=result["sql"],
            explanation=result["explanation"],
            tables_used=result["tables_used"],
            estimated_complexity=result["complexity"],
            warnings=[]
        )
    
    def _generate_demo_sql(self, intent: ParsedIntent) -> Dict:
        """Generate demo SQL based on intent"""
        
        # Build WHERE clause from filters
        where_clauses = []
        
        if intent.filters.get("status") == "active":
            where_clauses.append("status = 'active'")
        if intent.filters.get("region") == "northeast":
            where_clauses.append("region IN ('NY', 'NJ', 'CT', 'MA', 'PA')")
        if intent.filters.get("tier") == "enterprise":
            where_clauses.append("customer_tier = 'enterprise'")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Build SQL based on intent type
        if intent.intent_type == QueryIntent.AGGREGATION:
            if "count" in intent.metrics:
                sql = f"""SELECT 
    COUNT(DISTINCT customer_id) AS customer_count
FROM customers
WHERE {where_clause}
    AND type = 'customer'"""
            elif "revenue" in intent.metrics:
                sql = f"""SELECT 
    SUM(invoice_amount) AS total_revenue
FROM invoices i
JOIN customers c ON i.customer_id = c.customer_id
WHERE i.paid = true
    AND {where_clause}"""
            else:
                sql = f"SELECT COUNT(*) FROM customers WHERE {where_clause}"
                
        elif intent.intent_type == QueryIntent.LISTING:
            sql = f"""SELECT 
    customer_id,
    name,
    email,
    region,
    customer_tier,
    created_at
FROM customers
WHERE {where_clause}
ORDER BY created_at DESC
LIMIT 100"""
            
        else:
            sql = f"SELECT COUNT(*) FROM customers WHERE {where_clause}"
        
        return {
            "sql": sql,
            "explanation": f"Query to get data based on filters: {intent.filters}",
            "tables_used": ["customers"],
            "complexity": "low"
        }


# ============================================================================
# GUARDRAILS
# ============================================================================

class QueryGuardrails:
    """
    Validates and sanitizes SQL queries before execution.
    This is CRITICAL for security.
    """
    
    def __init__(self, config: SQLConfig, schema_manager: SchemaManager):
        self.config = config
        self.schema_manager = schema_manager
    
    def validate(self, query: GeneratedQuery) -> Tuple[bool, List[str]]:
        """
        Validate a generated SQL query.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        sql_upper = query.sql.upper()
        
        # Check for blocked operations
        for op in self.config.blocked_operations:
            # Use word boundary check to avoid false positives
            pattern = r'\b' + op + r'\b'
            if re.search(pattern, sql_upper):
                errors.append(f"Blocked operation detected: {op}")
        
        # Check table references
        for table in query.tables_used:
            if not self.schema_manager.validate_table(table):
                errors.append(f"Unknown table: {table}")
        
        # Check query complexity
        join_count = sql_upper.count(" JOIN ")
        if join_count > self.config.max_joins:
            errors.append(f"Too many JOINs: {join_count} (max: {self.config.max_joins})")
        
        subquery_count = sql_upper.count("SELECT") - 1
        if subquery_count > self.config.max_subqueries:
            errors.append(f"Too many subqueries: {subquery_count} (max: {self.config.max_subqueries})")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            (r';\s*SELECT', "Multiple statements detected"),
            (r'--', "SQL comment detected"),
            (r'/\*', "Block comment detected"),
            (r'UNION\s+SELECT', "UNION injection attempt"),
            (r'INTO\s+OUTFILE', "File write attempt"),
            (r'LOAD_FILE', "File read attempt"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, sql_upper):
                errors.append(message)
        
        # Ensure LIMIT clause exists
        if "LIMIT" not in sql_upper:
            query.warnings.append("No LIMIT clause - adding default limit")
            query.sql = query.sql.rstrip(';') + f"\nLIMIT {self.config.max_rows}"
        
        return len(errors) == 0, errors
    
    def apply_row_level_security(
        self, 
        query: GeneratedQuery, 
        user_context: Dict
    ) -> GeneratedQuery:
        """
        Apply row-level security based on user permissions.
        """
        if not self.config.enable_row_level_security:
            return query
        
        # Get user's allowed regions/departments
        allowed_regions = user_context.get("allowed_regions", [])
        
        if allowed_regions:
            # Inject RLS filter
            region_filter = f"region IN ({', '.join(repr(r) for r in allowed_regions)})"
            
            # Simple injection (in production: use proper SQL parsing)
            if "WHERE" in query.sql.upper():
                query.sql = query.sql.replace(
                    "WHERE", 
                    f"WHERE {region_filter} AND "
                )
            else:
                query.sql = query.sql.rstrip(';') + f"\nWHERE {region_filter}"
        
        return query


# ============================================================================
# QUERY EXECUTOR
# ============================================================================

class QueryExecutor:
    """
    Executes validated SQL queries against the database.
    """
    
    def __init__(self, config: SQLConfig):
        self.config = config
        self.connection = None
    
    def connect(self, connection_string: str):
        """Establish database connection"""
        # In production: use psycopg2 or sqlalchemy
        """
        import psycopg2
        self.connection = psycopg2.connect(connection_string)
        """
        pass
    
    def execute(self, query: GeneratedQuery) -> QueryResult:
        """Execute query and return results"""
        
        start_time = time.time()
        query_id = hashlib.md5(query.sql.encode()).hexdigest()[:12]
        
        # In production: execute against real database
        """
        with self.connection.cursor() as cursor:
            cursor.execute(query.sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            data = [dict(zip(columns, row)) for row in rows]
        """
        
        # Demo data
        data = [
            {"customer_count": 12847}
        ]
        columns = ["customer_count"]
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return QueryResult(
            data=data,
            columns=columns,
            row_count=len(data),
            execution_time_ms=execution_time,
            query_id=query_id,
            cached=False
        )


# ============================================================================
# MAIN CHAT-TO-SQL PIPELINE
# ============================================================================

class ChatToSQLPipeline:
    """
    Complete Chat-to-SQL pipeline that orchestrates all components.
    """
    
    def __init__(self, config: Optional[SQLConfig] = None):
        self.config = config or SQLConfig()
        
        # Initialize components
        self.semantic_layer = SemanticLayer()
        self.schema_manager = SchemaManager()
        self.intent_parser = IntentParser(self.config, self.semantic_layer)
        self.sql_generator = SQLGenerator(
            self.config, 
            self.semantic_layer, 
            self.schema_manager
        )
        self.guardrails = QueryGuardrails(self.config, self.schema_manager)
        self.executor = QueryExecutor(self.config)
        
        print("Chat-to-SQL Pipeline initialized")
        print(f"  - LLM model: {self.config.llm_model}")
        print(f"  - Max rows: {self.config.max_rows}")
        print(f"  - Blocked operations: {self.config.blocked_operations}")
    
    def query(
        self, 
        natural_query: str,
        user_context: Optional[Dict] = None
    ) -> ChatToSQLResponse:
        """
        Process a natural language query end-to-end.
        """
        user_context = user_context or {}
        
        print(f"\n💬 Query: {natural_query}")
        
        # Step 1: Parse intent
        print("  → Parsing intent...")
        intent = self.intent_parser.parse(natural_query)
        print(f"    Intent: {intent.intent_type.value}")
        print(f"    Metrics: {intent.metrics}")
        print(f"    Filters: {intent.filters}")
        
        # Step 2: Generate SQL
        print("  → Generating SQL...")
        generated = self.sql_generator.generate(intent, natural_query)
        print(f"    Tables: {generated.tables_used}")
        print(f"    Complexity: {generated.estimated_complexity}")
        
        # Step 3: Validate with guardrails
        print("  → Validating query...")
        is_valid, errors = self.guardrails.validate(generated)
        
        if not is_valid:
            print(f"    ❌ Validation failed: {errors}")
            return ChatToSQLResponse(
                natural_query=natural_query,
                parsed_intent=intent,
                generated_sql=generated,
                result=None,
                error=f"Query validation failed: {errors}"
            )
        
        print("    ✓ Query validated")
        
        # Step 4: Apply row-level security
        if self.config.enable_row_level_security:
            print("  → Applying row-level security...")
            generated = self.guardrails.apply_row_level_security(
                generated, 
                user_context
            )
        
        # Step 5: Execute query
        print("  → Executing query...")
        result = self.executor.execute(generated)
        print(f"    Rows returned: {result.row_count}")
        print(f"    Execution time: {result.execution_time_ms}ms")
        
        print("  ✅ Query complete")
        
        return ChatToSQLResponse(
            natural_query=natural_query,
            parsed_intent=intent,
            generated_sql=generated,
            result=result,
            error=None
        )
    
    def explain(self, natural_query: str) -> str:
        """
        Explain what SQL would be generated without executing.
        """
        intent = self.intent_parser.parse(natural_query)
        generated = self.sql_generator.generate(intent, natural_query)
        
        return f"""
Query Explanation:
==================

Original Question: {natural_query}

Parsed Intent:
- Type: {intent.intent_type.value}
- Metrics: {intent.metrics}
- Filters: {intent.filters}

Generated SQL:
{generated.sql}

Explanation: {generated.explanation}
Tables Used: {', '.join(generated.tables_used)}
Complexity: {generated.estimated_complexity}
"""


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def main():
    """Demonstrate the Chat-to-SQL pipeline"""
    
    print("=" * 70)
    print("CHAT-TO-SQL SYSTEM - DEMO")
    print("=" * 70)
    
    # Initialize pipeline
    config = SQLConfig(
        max_rows=1000,
        enable_row_level_security=True
    )
    
    pipeline = ChatToSQLPipeline(config)
    
    # User context (from authentication)
    user_context = {
        "user_id": "user_123",
        "role": "analyst",
        "allowed_regions": ["NY", "NJ", "CT", "MA", "PA"]
    }
    
    # Test queries
    print("\n" + "=" * 70)
    print("RUNNING QUERIES")
    print("=" * 70)
    
    queries = [
        "How many active customers do we have in the northeast?",
        "What's our total revenue from enterprise customers?",
        "Show me all customers created this month",
        "Compare revenue between northeast and west coast"
    ]
    
    for query in queries:
        response = pipeline.query(query, user_context)
        
        print("\n" + "-" * 50)
        print(f"Q: {query}")
        print("-" * 50)
        
        if response.error:
            print(f"❌ Error: {response.error}")
        else:
            print(f"\n📊 Generated SQL:")
            print(response.generated_sql.sql)
            print(f"\n📝 Explanation: {response.generated_sql.explanation}")
            
            if response.result:
                print(f"\n✅ Result: {response.result.data}")
                print(f"⏱️  Execution time: {response.result.execution_time_ms}ms")
    
    # Show explanation feature
    print("\n" + "=" * 70)
    print("EXPLAIN FEATURE")
    print("=" * 70)
    
    explanation = pipeline.explain(
        "How many churned enterprise customers do we have?"
    )
    print(explanation)
    
    # Demonstrate guardrails
    print("\n" + "=" * 70)
    print("GUARDRAILS DEMO - BLOCKED QUERIES")
    print("=" * 70)
    
    # This would be caught by guardrails
    malicious_query = "Delete all customers from the northeast"
    response = pipeline.query(malicious_query, user_context)
    
    if response.error:
        print(f"✅ Blocked malicious query: {response.error}")


if __name__ == "__main__":
    main()
