"""
JOVIAL (J73) Semantic Parser - Builds AST and Semantic Model
Based on MIL-STD-1589B/C specifications

This parser builds a semantic model for JOVIAL J73 code, enabling:
- Item (variable) tracking and type inference
- Table (array/structure) analysis
- PROC (procedure) signatures
- COMPOOL (communication pool) references
- Scope resolution for IDE features
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class JovialType(Enum):
    """JOVIAL J73 data types"""
    SIGNED = "S"           # Signed integer
    UNSIGNED = "U"         # Unsigned integer
    FLOAT = "F"            # Floating point
    FIXED = "A"            # Fixed point (scaled)
    BIT = "B"              # Bit string
    CHARACTER = "C"        # Character string
    STATUS = "STATUS"      # Enumeration
    POINTER = "P"          # Pointer
    TABLE = "TABLE"        # Table (array/struct)
    ENTRY = "ENTRY"        # Table entry
    UNKNOWN = "UNKNOWN"


@dataclass
class ItemDefinition:
    """Represents a JOVIAL ITEM (variable) declaration"""
    name: str
    type: JovialType
    size: Optional[int] = None          # Bit size for S/U/B, precision for F, length for C
    scale: Optional[int] = None         # For fixed-point (A type)
    status_values: List[str] = field(default_factory=list)  # For STATUS type
    is_constant: bool = False
    is_static: bool = False
    is_parallel: bool = False           # PARALLEL allocation
    initial_value: Optional[str] = None
    position: Optional[Tuple[int, int]] = None  # POS(bit, word) for OVERLAY
    line_number: int = 0
    column_start: int = 0
    column_end: int = 0
    parent_table: Optional[str] = None  # If item is within a table


@dataclass
class TableDefinition:
    """Represents a JOVIAL TABLE declaration"""
    name: str
    dimensions: List[Tuple[int, int]] = field(default_factory=list)  # (lower, upper) bounds
    entries: Dict[str, ItemDefinition] = field(default_factory=dict)  # Items within table
    is_constant: bool = False
    is_static: bool = False
    is_parallel: bool = False
    wordsize: Optional[int] = None      # W attribute
    line_start: int = 0
    line_end: int = 0


@dataclass
class ProcDefinition:
    """Represents a JOVIAL PROC (procedure) declaration"""
    name: str
    parameters: List[Tuple[str, str]] = field(default_factory=list)  # (name, mode: IN/OUT/INOUT)
    return_type: Optional[JovialType] = None  # For function PROCs
    is_recursive: bool = False
    is_reentrant: bool = False
    local_items: Dict[str, ItemDefinition] = field(default_factory=dict)
    local_tables: Dict[str, TableDefinition] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0
    body_start: int = 0


@dataclass
class CompoolReference:
    """Represents a COMPOOL reference"""
    name: str
    items: Set[str] = field(default_factory=set)      # DEF items from compool
    tables: Set[str] = field(default_factory=set)     # DEF tables from compool
    procs: Set[str] = field(default_factory=set)      # DEF procs from compool
    line_number: int = 0


@dataclass
class DefineConstant:
    """Represents a DEFINE constant"""
    name: str
    value: str
    line_number: int = 0


class JovialSemanticModel:
    """
    Semantic model of a JOVIAL program
    Tracks items, tables, procs, compools, and scopes
    """

    def __init__(self):
        self.items: Dict[str, ItemDefinition] = {}
        self.tables: Dict[str, TableDefinition] = {}
        self.procs: Dict[str, ProcDefinition] = {}
        self.compools: Dict[str, CompoolReference] = {}
        self.defines: Dict[str, DefineConstant] = {}
        self.types: Dict[str, Any] = {}  # User-defined TYPE declarations

        self.current_scope: str = "GLOBAL"
        self.scope_stack: List[str] = []
        self.program_name: Optional[str] = None
        self.module_type: Optional[str] = None  # PROC, COMPOOL, or MAIN

    def add_item(self, item: ItemDefinition):
        """Add an item definition"""
        key = f"{self.current_scope}.{item.name}" if self.current_scope != "GLOBAL" else item.name
        self.items[item.name] = item
        self.items[key] = item

    def get_item(self, name: str) -> Optional[ItemDefinition]:
        """Get item by name, checking scopes"""
        # Check current scope first
        scoped_name = f"{self.current_scope}.{name}"
        if scoped_name in self.items:
            return self.items[scoped_name]
        # Check global
        if name in self.items:
            return self.items[name]
        return None

    def add_table(self, table: TableDefinition):
        """Add a table definition"""
        self.tables[table.name] = table

    def get_table(self, name: str) -> Optional[TableDefinition]:
        """Get table by name"""
        return self.tables.get(name)

    def add_proc(self, proc: ProcDefinition):
        """Add a procedure definition"""
        self.procs[proc.name] = proc

    def get_proc(self, name: str) -> Optional[ProcDefinition]:
        """Get procedure by name"""
        return self.procs.get(name)

    def get_all_symbols(self) -> List[str]:
        """Get all symbol names for completion"""
        symbols = []
        symbols.extend(self.items.keys())
        symbols.extend(self.tables.keys())
        symbols.extend(self.procs.keys())
        symbols.extend(self.defines.keys())
        return list(set(symbols))


class JovialSemanticParser:
    """
    Parses JOVIAL J73 code and builds a semantic model
    """

    # J73 Keywords
    KEYWORDS = {
        # Module structure
        'START', 'TERM', 'BEGIN', 'END', 'COMPOOL', 'PROGRAM',
        # Declarations
        'ITEM', 'TABLE', 'PROC', 'TYPE', 'DEFINE', 'DEF', 'REF',
        # Type abbreviations
        'S', 'U', 'F', 'A', 'B', 'C', 'P', 'STATUS', 'LIKE',
        # Attributes
        'STATIC', 'CONSTANT', 'PARALLEL', 'OVERLAY', 'POS', 'W', 'D',
        'ROUND', 'TRUNCATE', 'DENSE', 'BLOCK',
        # Control flow
        'IF', 'THEN', 'ELSE', 'FOR', 'BY', 'WHILE', 'UNTIL',
        'CASE', 'DEFAULT', 'FALLTHRU', 'GOTO', 'EXIT', 'ABORT', 'RETURN', 'STOP',
        # Operators
        'AND', 'OR', 'NOT', 'XOR', 'EQV', 'MOD', 'ABS', 'SGN',
        # Built-in functions
        'LOC', 'NEXT', 'BIT', 'BYTE', 'SHIFTL', 'SHIFTR', 'SHIFTLA', 'SHIFTRA',
        'FIRST', 'LAST', 'LBOUND', 'HBOUND', 'NENT', 'NWDSEN', 'BITSIZE', 'BYTESIZE', 'WORDSIZE',
        # I/O
        'INPUT', 'OUTPUT', 'OPEN', 'CLOSE',
    }

    # Status value pattern V(name)
    STATUS_VALUE_PATTERN = re.compile(r"V\s*\(\s*([A-Z][A-Z0-9']*)\s*\)", re.IGNORECASE)

    def __init__(self):
        self.model = JovialSemanticModel()
        self.lines: List[str] = []
        self.current_line_num = 0

        # Parser state
        self.in_table_body = False
        self.current_table: Optional[str] = None
        self.in_proc_body = False
        self.current_proc: Optional[str] = None
        self.in_compool = False

    def parse(self, jovial_code: str) -> JovialSemanticModel:
        """
        Parse JOVIAL code and return semantic model
        """
        self.model = JovialSemanticModel()
        self.lines = jovial_code.split('\n')
        self.current_line_num = 0

        # Reset state
        self.in_table_body = False
        self.current_table = None
        self.in_proc_body = False
        self.current_proc = None
        self.in_compool = False

        # Multi-line statement buffer
        statement_buffer = ""

        for i, line in enumerate(self.lines):
            self.current_line_num = i

            # Remove comments ($ to end of line in J73, or " quoted comments)
            line = self._remove_comments(line)

            stripped = line.strip()
            if not stripped:
                continue

            # Accumulate multi-line statements (until semicolon)
            statement_buffer += " " + stripped

            # Check if statement is complete (ends with semicolon or is a block marker)
            if stripped.endswith(';') or stripped.upper() in ('BEGIN', 'END', 'START', 'TERM'):
                self._parse_statement(statement_buffer.strip(), i)
                statement_buffer = ""

        return self.model

    def _remove_comments(self, line: str) -> str:
        """Remove J73 comments from a line"""
        # Inline comments start with "
        # Also $ can be comment in some contexts
        result = []
        in_string = False
        in_comment = False

        for i, char in enumerate(line):
            if in_comment:
                # Comment to end of line
                break
            elif char == '"' and not in_string:
                # Start of comment
                in_comment = True
            elif char == "'" and not in_comment:
                # Toggle string mode
                in_string = not in_string
                result.append(char)
            else:
                result.append(char)

        return ''.join(result)

    def _parse_statement(self, statement: str, line_num: int):
        """Parse a complete statement"""
        upper = statement.upper()

        # Module structure
        if upper.startswith('START'):
            self._parse_start(statement, line_num)
        elif upper.startswith('TERM'):
            pass  # End of module
        elif upper.startswith('COMPOOL'):
            self._parse_compool_start(statement, line_num)
        elif upper == 'BEGIN':
            self._handle_begin(line_num)
        elif upper == 'END':
            self._handle_end(line_num)

        # Declarations
        elif upper.startswith('ITEM'):
            self._parse_item_declaration(statement, line_num)
        elif upper.startswith('TABLE'):
            self._parse_table_declaration(statement, line_num)
        elif upper.startswith('PROC'):
            self._parse_proc_declaration(statement, line_num)
        elif upper.startswith('TYPE'):
            self._parse_type_declaration(statement, line_num)
        elif upper.startswith('DEFINE'):
            self._parse_define(statement, line_num)
        elif upper.startswith('DEF') and not upper.startswith('DEFINE'):
            self._parse_def_reference(statement, line_num)
        elif upper.startswith('REF'):
            self._parse_ref_reference(statement, line_num)

    def _parse_start(self, statement: str, line_num: int):
        """Parse START statement"""
        # START [program-name]
        match = re.match(r'START\s+([A-Z][A-Z0-9\']*)?', statement, re.IGNORECASE)
        if match and match.group(1):
            self.model.program_name = match.group(1)
        self.model.module_type = "MAIN"

    def _parse_compool_start(self, statement: str, line_num: int):
        """Parse COMPOOL module start"""
        match = re.match(r'COMPOOL\s+([A-Z][A-Z0-9\']*)', statement, re.IGNORECASE)
        if match:
            self.model.program_name = match.group(1)
            self.model.module_type = "COMPOOL"
        self.in_compool = True

    def _parse_item_declaration(self, statement: str, line_num: int):
        """Parse ITEM declaration"""
        # Patterns:
        # ITEM name S [size] [= value];
        # ITEM name STATUS (V(a), V(b), ...);
        # ITEM name type [attributes] [= value];

        # Remove trailing semicolon
        stmt = statement.rstrip(';').strip()

        # Basic pattern: ITEM name type-spec [attributes]
        match = re.match(
            r'ITEM\s+([A-Z][A-Z0-9\']*)\s+'
            r'(STATIC\s+|CONSTANT\s+|PARALLEL\s+)*'
            r'(S|U|F|A|B|C|P|STATUS)\s*'
            r'(\d+)?'
            r'(.*)',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1)
            attrs = match.group(2) or ""
            type_abbrev = match.group(3).upper()
            size = int(match.group(4)) if match.group(4) else None
            rest = match.group(5) or ""

            # Map type abbreviation to enum
            type_map = {
                'S': JovialType.SIGNED,
                'U': JovialType.UNSIGNED,
                'F': JovialType.FLOAT,
                'A': JovialType.FIXED,
                'B': JovialType.BIT,
                'C': JovialType.CHARACTER,
                'P': JovialType.POINTER,
                'STATUS': JovialType.STATUS,
            }
            item_type = type_map.get(type_abbrev, JovialType.UNKNOWN)

            # Parse STATUS values if present
            status_values = []
            if item_type == JovialType.STATUS:
                # Find V(name) patterns in the statement
                status_values = self.STATUS_VALUE_PATTERN.findall(statement)

            # Parse initial value if present
            initial_value = None
            value_match = re.search(r'=\s*(.+)$', rest)
            if value_match:
                initial_value = value_match.group(1).strip()

            # Create item definition
            item = ItemDefinition(
                name=name,
                type=item_type,
                size=size,
                status_values=status_values,
                is_constant='CONSTANT' in attrs.upper(),
                is_static='STATIC' in attrs.upper(),
                is_parallel='PARALLEL' in attrs.upper(),
                initial_value=initial_value,
                line_number=line_num,
                column_start=statement.upper().find(name),
                column_end=statement.upper().find(name) + len(name),
                parent_table=self.current_table
            )

            # Add to appropriate container
            if self.current_table and self.in_table_body:
                table = self.model.get_table(self.current_table)
                if table:
                    table.entries[name] = item
            elif self.current_proc and self.in_proc_body:
                proc = self.model.get_proc(self.current_proc)
                if proc:
                    proc.local_items[name] = item

            self.model.add_item(item)

    def _parse_table_declaration(self, statement: str, line_num: int):
        """Parse TABLE declaration"""
        # TABLE name (bounds) [attributes];
        # TABLE name (lower:upper, lower:upper) [W size];

        stmt = statement.rstrip(';').strip()

        # Match table header
        match = re.match(
            r'TABLE\s+([A-Z][A-Z0-9\']*)\s*'
            r'\(([^)]+)\)\s*'
            r'(.*)',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1)
            dims_str = match.group(2)
            attrs = match.group(3) or ""

            # Parse dimensions
            dimensions = []
            dim_parts = dims_str.split(',')
            for dim in dim_parts:
                dim = dim.strip()
                if ':' in dim:
                    parts = dim.split(':')
                    lower = int(parts[0].strip()) if parts[0].strip().lstrip('-').isdigit() else 0
                    upper = int(parts[1].strip()) if parts[1].strip().lstrip('-').isdigit() else 0
                    dimensions.append((lower, upper))
                else:
                    # Single bound means 0 to n or 1 to n
                    upper = int(dim) if dim.isdigit() else 0
                    dimensions.append((1, upper))

            # Parse wordsize (W attribute)
            wordsize = None
            w_match = re.search(r'W\s+(\d+)', attrs, re.IGNORECASE)
            if w_match:
                wordsize = int(w_match.group(1))

            table = TableDefinition(
                name=name,
                dimensions=dimensions,
                is_constant='CONSTANT' in attrs.upper(),
                is_static='STATIC' in attrs.upper(),
                is_parallel='PARALLEL' in attrs.upper(),
                wordsize=wordsize,
                line_start=line_num,
            )

            self.model.add_table(table)
            self.current_table = name

    def _parse_proc_declaration(self, statement: str, line_num: int):
        """Parse PROC declaration"""
        # PROC name (params);
        # PROC name (in1, in2 : out1, out2);

        stmt = statement.rstrip(';').strip()

        match = re.match(
            r'PROC\s+([A-Z][A-Z0-9\']*)\s*'
            r'(?:\(([^)]*)\))?\s*'
            r'(.*)',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1)
            params_str = match.group(2) or ""
            rest = match.group(3) or ""

            # Parse parameters (input : output)
            parameters = []
            if params_str:
                if ':' in params_str:
                    # Split into input and output sections
                    in_out = params_str.split(':')
                    inputs = [p.strip() for p in in_out[0].split(',') if p.strip()]
                    outputs = [p.strip() for p in in_out[1].split(',') if p.strip()] if len(in_out) > 1 else []

                    for p in inputs:
                        parameters.append((p, 'IN'))
                    for p in outputs:
                        parameters.append((p, 'OUT'))
                else:
                    # All parameters (mode determined by usage)
                    for p in params_str.split(','):
                        p = p.strip()
                        if p:
                            parameters.append((p, 'INOUT'))

            proc = ProcDefinition(
                name=name,
                parameters=parameters,
                line_start=line_num,
            )

            self.model.add_proc(proc)
            self.current_proc = name

    def _parse_type_declaration(self, statement: str, line_num: int):
        """Parse TYPE declaration"""
        # TYPE typename type-description;
        stmt = statement.rstrip(';').strip()

        match = re.match(
            r'TYPE\s+([A-Z][A-Z0-9\']*)\s+(.+)',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1)
            type_desc = match.group(2)
            self.model.types[name] = {
                'name': name,
                'description': type_desc,
                'line': line_num
            }

    def _parse_define(self, statement: str, line_num: int):
        """Parse DEFINE constant"""
        # DEFINE name value;
        # DEFINE name = value;
        stmt = statement.rstrip(';').strip()

        match = re.match(
            r'DEFINE\s+([A-Z][A-Z0-9\']*)\s*=?\s*(.+)',
            stmt, re.IGNORECASE
        )

        if match:
            name = match.group(1)
            value = match.group(2)
            self.model.defines[name] = DefineConstant(
                name=name,
                value=value,
                line_number=line_num
            )

    def _parse_def_reference(self, statement: str, line_num: int):
        """Parse DEF (import from COMPOOL)"""
        # DEF name;
        # DEF ITEM name;
        # DEF TABLE name;
        # DEF PROC name;
        stmt = statement.rstrip(';').strip()

        match = re.match(
            r'DEF\s+(ITEM|TABLE|PROC)?\s*([A-Z][A-Z0-9\']*)',
            stmt, re.IGNORECASE
        )

        if match:
            kind = match.group(1).upper() if match.group(1) else None
            name = match.group(2)

            # Create placeholder for imported symbol
            if kind == 'ITEM' or kind is None:
                item = ItemDefinition(
                    name=name,
                    type=JovialType.UNKNOWN,
                    line_number=line_num
                )
                self.model.add_item(item)

    def _parse_ref_reference(self, statement: str, line_num: int):
        """Parse REF (reference to external)"""
        # REF PROC name;
        stmt = statement.rstrip(';').strip()

        match = re.match(
            r'REF\s+(ITEM|TABLE|PROC)?\s*([A-Z][A-Z0-9\']*)',
            stmt, re.IGNORECASE
        )

        if match:
            kind = match.group(1).upper() if match.group(1) else 'PROC'
            name = match.group(2)

            if kind == 'PROC':
                proc = ProcDefinition(
                    name=name,
                    line_start=line_num
                )
                self.model.add_proc(proc)

    def _handle_begin(self, line_num: int):
        """Handle BEGIN block marker"""
        if self.current_table:
            self.in_table_body = True
        if self.current_proc:
            self.in_proc_body = True
            proc = self.model.get_proc(self.current_proc)
            if proc:
                proc.body_start = line_num

    def _handle_end(self, line_num: int):
        """Handle END block marker"""
        if self.in_table_body:
            self.in_table_body = False
            if self.current_table:
                table = self.model.get_table(self.current_table)
                if table:
                    table.line_end = line_num
            self.current_table = None
        elif self.in_proc_body:
            self.in_proc_body = False
            if self.current_proc:
                proc = self.model.get_proc(self.current_proc)
                if proc:
                    proc.line_end = line_num
            self.current_proc = None

    def get_completions_at_position(self, line: int, column: int) -> List[str]:
        """Get completion suggestions at a specific position"""
        if line < 0 or line >= len(self.lines):
            return []

        current_line = self.lines[line]
        prefix = current_line[:column].strip().split()[-1] if current_line[:column].strip() else ""
        prefix = prefix.upper()

        completions = []

        # Add keywords
        for kw in self.KEYWORDS:
            if not prefix or kw.startswith(prefix):
                completions.append(kw)

        # Add symbols from model
        for symbol in self.model.get_all_symbols():
            if not prefix or symbol.upper().startswith(prefix):
                completions.append(symbol)

        return sorted(set(completions))

    def get_hover_info(self, line: int, column: int) -> Optional[Dict]:
        """Get hover information at a specific position"""
        if line < 0 or line >= len(self.lines):
            return None

        current_line = self.lines[line]

        # Find word at position
        word_match = None
        for match in re.finditer(r"\b([A-Z][A-Z0-9']*)\b", current_line, re.IGNORECASE):
            if match.start() <= column <= match.end():
                word_match = match
                break

        if not word_match:
            return None

        word = word_match.group(1).upper()

        # Check if it's an item
        item = self.model.get_item(word)
        if item:
            return {
                'type': 'item',
                'name': item.name,
                'jovial_type': item.type.value,
                'size': item.size,
                'is_constant': item.is_constant,
                'is_static': item.is_static,
                'status_values': item.status_values,
                'initial_value': item.initial_value,
                'line': item.line_number
            }

        # Check if it's a table
        table = self.model.get_table(word)
        if table:
            dim_str = ', '.join([f"{d[0]}:{d[1]}" for d in table.dimensions])
            return {
                'type': 'table',
                'name': table.name,
                'dimensions': dim_str,
                'entries': list(table.entries.keys()),
                'wordsize': table.wordsize,
                'line_start': table.line_start,
                'line_end': table.line_end
            }

        # Check if it's a proc
        proc = self.model.get_proc(word)
        if proc:
            params_str = ', '.join([f"{p[0]} ({p[1]})" for p in proc.parameters])
            return {
                'type': 'proc',
                'name': proc.name,
                'parameters': params_str,
                'line_start': proc.line_start,
                'line_end': proc.line_end
            }

        # Check if it's a keyword
        if word in self.KEYWORDS:
            return {
                'type': 'keyword',
                'name': word,
                'description': self._get_keyword_description(word)
            }

        return None

    def _get_keyword_description(self, keyword: str) -> str:
        """Get description for a J73 keyword"""
        descriptions = {
            'START': 'Begin main program module',
            'TERM': 'End program module',
            'BEGIN': 'Begin block',
            'END': 'End block',
            'COMPOOL': 'Communication pool module (shared data)',
            'ITEM': 'Scalar variable declaration',
            'TABLE': 'Array/structure declaration',
            'PROC': 'Procedure declaration',
            'TYPE': 'User-defined type declaration',
            'DEFINE': 'Compile-time constant',
            'DEF': 'Import from COMPOOL',
            'REF': 'Reference to external',
            'S': 'Signed integer type',
            'U': 'Unsigned integer type',
            'F': 'Floating-point type',
            'A': 'Fixed-point (scaled) type',
            'B': 'Bit string type',
            'C': 'Character string type',
            'P': 'Pointer type',
            'STATUS': 'Enumeration type',
            'STATIC': 'Static allocation (persistent)',
            'CONSTANT': 'Read-only value',
            'PARALLEL': 'Parallel allocation for bit-packing',
            'IF': 'Conditional statement',
            'FOR': 'Counted loop',
            'WHILE': 'Conditional loop (test before)',
            'UNTIL': 'Conditional loop (test after)',
            'CASE': 'Multi-way branch',
            'GOTO': 'Unconditional branch',
            'RETURN': 'Return from procedure',
            'EXIT': 'Exit from loop',
            'ABORT': 'Abort program execution',
            'LOC': 'Location (address) function',
            'NEXT': 'Next value in sequence',
            'BIT': 'Bit extraction function',
            'BYTE': 'Byte extraction function',
            'SHIFTL': 'Shift left',
            'SHIFTR': 'Shift right',
        }
        return descriptions.get(keyword, f'J73 keyword: {keyword}')


# Example usage and test
if __name__ == '__main__':
    test_code = '''
START FLIGHT'CONTROL;

DEFINE MAX'ALTITUDE = 50000;

" Data declarations "
ITEM ALTITUDE STATIC S 16;
ITEM AIRSPEED F 32;
ITEM HEADING U 9;
ITEM STATUS'FLAG STATUS (V(NORMAL), V(WARNING), V(CRITICAL));
ITEM PILOT'NAME C 30;

TABLE WAYPOINTS (1:100);
BEGIN
    ITEM LAT F 32;
    ITEM LON F 32;
    ITEM ALT S 16;
END

PROC UPDATE'POSITION (NEW'LAT, NEW'LON : DISTANCE);
BEGIN
    ITEM NEW'LAT F;
    ITEM NEW'LON F;
    ITEM DISTANCE F;

    " Calculate distance and update "
END

TERM
'''

    parser = JovialSemanticParser()
    model = parser.parse(test_code)

    print("=" * 60)
    print("JOVIAL J73 Semantic Parser Test")
    print("=" * 60)

    print(f"\nProgram: {model.program_name}")
    print(f"Module type: {model.module_type}")

    print(f"\nItems ({len(model.items)}):")
    for name, item in model.items.items():
        if '.' not in name:  # Skip scoped duplicates
            print(f"  {name}: {item.type.value} {item.size or ''}")
            if item.status_values:
                print(f"    Values: {item.status_values}")

    print(f"\nTables ({len(model.tables)}):")
    for name, table in model.tables.items():
        dims = ', '.join([f"{d[0]}:{d[1]}" for d in table.dimensions])
        print(f"  {name} ({dims})")
        for entry_name, entry in table.entries.items():
            print(f"    .{entry_name}: {entry.type.value}")

    print(f"\nProcs ({len(model.procs)}):")
    for name, proc in model.procs.items():
        params = ', '.join([f"{p[0]}({p[1]})" for p in proc.parameters])
        print(f"  {name} ({params})")

    print(f"\nDefines ({len(model.defines)}):")
    for name, define in model.defines.items():
        print(f"  {name} = {define.value}")
