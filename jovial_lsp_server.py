"""
JOVIAL (J73) Language Server Protocol (LSP) Server
Based on MIL-STD-1589B/C specifications

Implements LSP for JOVIAL J73, enabling IDE features:
- Code completion
- Hover information
- Go to definition
- Find references
- Document symbols
- Diagnostics
"""

import json
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from jovial_semantic_parser import JovialSemanticParser, JovialSemanticModel, JovialType


@dataclass
class LSPPosition:
    """LSP position (line, character)"""
    line: int
    character: int

    @classmethod
    def from_dict(cls, data: Dict) -> 'LSPPosition':
        return cls(line=data['line'], character=data['character'])

    def to_dict(self) -> Dict:
        return {'line': self.line, 'character': self.character}


@dataclass
class LSPRange:
    """LSP range (start, end positions)"""
    start: LSPPosition
    end: LSPPosition

    @classmethod
    def from_dict(cls, data: Dict) -> 'LSPRange':
        return cls(
            start=LSPPosition.from_dict(data['start']),
            end=LSPPosition.from_dict(data['end'])
        )

    def to_dict(self) -> Dict:
        return {
            'start': self.start.to_dict(),
            'end': self.end.to_dict()
        }


@dataclass
class LSPLocation:
    """LSP location (URI + range)"""
    uri: str
    range: LSPRange

    def to_dict(self) -> Dict:
        return {
            'uri': self.uri,
            'range': self.range.to_dict()
        }


class JovialLSPServer:
    """
    LSP Server for JOVIAL J73
    Handles LSP requests and responses
    """

    def __init__(self):
        self.parser = JovialSemanticParser()
        self.documents: Dict[str, str] = {}  # URI -> document content
        self.models: Dict[str, JovialSemanticModel] = {}  # URI -> semantic model

    def handle_request(self, request: Dict) -> Optional[Dict]:
        """Handle an LSP request"""
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')

        if method == 'initialize':
            return self._handle_initialize(request_id)
        elif method == 'initialized':
            return None  # Notification
        elif method == 'textDocument/didOpen':
            self._handle_did_open(params)
            return None
        elif method == 'textDocument/didChange':
            self._handle_did_change(params)
            return None
        elif method == 'textDocument/didClose':
            self._handle_did_close(params)
            return None
        elif method == 'textDocument/completion':
            return self._handle_completion(request_id, params)
        elif method == 'textDocument/hover':
            return self._handle_hover(request_id, params)
        elif method == 'textDocument/definition':
            return self._handle_definition(request_id, params)
        elif method == 'textDocument/references':
            return self._handle_references(request_id, params)
        elif method == 'textDocument/documentSymbol':
            return self._handle_document_symbol(request_id, params)
        elif method == 'shutdown':
            return {'jsonrpc': '2.0', 'id': request_id, 'result': None}
        else:
            if request_id:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }
            return None

    def _handle_initialize(self, request_id: Optional[int]) -> Dict:
        """Handle initialize request"""
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'capabilities': {
                    'textDocumentSync': {
                        'openClose': True,
                        'change': 1  # Full sync
                    },
                    'completionProvider': {
                        'triggerCharacters': [' ', "'", '.', '(']
                    },
                    'hoverProvider': True,
                    'definitionProvider': True,
                    'referencesProvider': True,
                    'documentSymbolProvider': True,
                },
                'serverInfo': {
                    'name': 'JOVIAL J73 LSP Server',
                    'version': '1.0.0'
                }
            }
        }

    def _handle_did_open(self, params: Dict):
        """Handle textDocument/didOpen notification"""
        uri = params['textDocument']['uri']
        text = params['textDocument']['text']
        self.documents[uri] = text
        self._parse_document(uri)

    def _handle_did_change(self, params: Dict):
        """Handle textDocument/didChange notification"""
        uri = params['textDocument']['uri']
        changes = params['contentChanges']

        if changes:
            # Full sync - take last change
            self.documents[uri] = changes[-1].get('text', '')
            self._parse_document(uri)

    def _handle_did_close(self, params: Dict):
        """Handle textDocument/didClose notification"""
        uri = params['textDocument']['uri']
        if uri in self.documents:
            del self.documents[uri]
        if uri in self.models:
            del self.models[uri]

    def _parse_document(self, uri: str):
        """Parse a document and build semantic model"""
        if uri not in self.documents:
            return

        text = self.documents[uri]
        parser = JovialSemanticParser()
        model = parser.parse(text)
        self.models[uri] = model

    def _handle_completion(self, request_id: Optional[int], params: Dict) -> Dict:
        """Handle textDocument/completion request"""
        uri = params['textDocument']['uri']
        position = LSPPosition.from_dict(params['position'])

        if uri not in self.models:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {'isIncomplete': False, 'items': []}
            }

        model = self.models[uri]
        parser = JovialSemanticParser()
        parser.model = model
        parser.lines = self.documents[uri].split('\n')

        completions = parser.get_completions_at_position(position.line, position.character)

        items = []
        for i, completion in enumerate(completions):
            # Determine kind based on what it is
            kind = 6  # Variable (default)
            detail = 'JOVIAL symbol'

            if completion in parser.KEYWORDS:
                kind = 14  # Keyword
                detail = 'J73 keyword'
            elif completion in model.procs:
                kind = 3  # Function
                proc = model.procs[completion]
                params_str = ', '.join([p[0] for p in proc.parameters])
                detail = f'PROC ({params_str})'
            elif completion in model.tables:
                kind = 7  # Class (for table/struct)
                table = model.tables[completion]
                dims = ', '.join([f"{d[0]}:{d[1]}" for d in table.dimensions])
                detail = f'TABLE ({dims})'
            elif completion in model.items:
                item = model.items[completion]
                kind = 6  # Variable
                type_str = item.type.value
                if item.size:
                    type_str += f' {item.size}'
                detail = f'ITEM {type_str}'
            elif completion in model.defines:
                kind = 21  # Constant
                detail = f'DEFINE = {model.defines[completion].value}'

            items.append({
                'label': completion,
                'kind': kind,
                'detail': detail,
                'insertText': completion,
                'sortText': f'{i:04d}'
            })

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'isIncomplete': False,
                'items': items
            }
        }

    def _handle_hover(self, request_id: Optional[int], params: Dict) -> Dict:
        """Handle textDocument/hover request"""
        uri = params['textDocument']['uri']
        position = LSPPosition.from_dict(params['position'])

        if uri not in self.models:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': None
            }

        model = self.models[uri]
        parser = JovialSemanticParser()
        parser.model = model
        parser.lines = self.documents[uri].split('\n')

        hover_info = parser.get_hover_info(position.line, position.character)

        if not hover_info:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': None
            }

        # Build hover content in markdown
        if hover_info['type'] == 'item':
            content = f"**{hover_info['name']}** (ITEM)\n\n"
            content += f"Type: `{hover_info['jovial_type']}`"
            if hover_info.get('size'):
                content += f" {hover_info['size']}"
            content += "\n"
            if hover_info.get('is_constant'):
                content += "Attribute: `CONSTANT`\n"
            if hover_info.get('is_static'):
                content += "Attribute: `STATIC`\n"
            if hover_info.get('status_values'):
                content += f"Values: {', '.join(hover_info['status_values'])}\n"
            if hover_info.get('initial_value'):
                content += f"Initial: `{hover_info['initial_value']}`\n"
            content += f"\nDefined at line {hover_info['line'] + 1}"

        elif hover_info['type'] == 'table':
            content = f"**{hover_info['name']}** (TABLE)\n\n"
            content += f"Dimensions: `({hover_info['dimensions']})`\n"
            if hover_info.get('wordsize'):
                content += f"Word size: {hover_info['wordsize']}\n"
            if hover_info.get('entries'):
                content += f"\nEntries:\n"
                for entry in hover_info['entries'][:10]:  # Limit display
                    content += f"- {entry}\n"
            content += f"\nLines {hover_info['line_start'] + 1}-{hover_info.get('line_end', hover_info['line_start']) + 1}"

        elif hover_info['type'] == 'proc':
            content = f"**{hover_info['name']}** (PROC)\n\n"
            if hover_info.get('parameters'):
                content += f"Parameters: `{hover_info['parameters']}`\n"
            content += f"\nLines {hover_info['line_start'] + 1}-{hover_info.get('line_end', hover_info['line_start']) + 1}"

        elif hover_info['type'] == 'keyword':
            content = f"**{hover_info['name']}** (J73 Keyword)\n\n"
            content += hover_info.get('description', '')

        else:
            content = str(hover_info)

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': {
                'contents': {
                    'kind': 'markdown',
                    'value': content
                }
            }
        }

    def _handle_definition(self, request_id: Optional[int], params: Dict) -> Dict:
        """Handle textDocument/definition request"""
        uri = params['textDocument']['uri']
        position = LSPPosition.from_dict(params['position'])

        if uri not in self.models:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': None
            }

        model = self.models[uri]
        parser = JovialSemanticParser()
        parser.model = model
        parser.lines = self.documents[uri].split('\n')

        hover_info = parser.get_hover_info(position.line, position.character)

        if not hover_info:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': None
            }

        # Get definition line
        def_line = None
        if hover_info['type'] == 'item':
            def_line = hover_info.get('line', 0)
        elif hover_info['type'] == 'table':
            def_line = hover_info.get('line_start', 0)
        elif hover_info['type'] == 'proc':
            def_line = hover_info.get('line_start', 0)

        if def_line is None:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': None
            }

        location = LSPLocation(
            uri=uri,
            range=LSPRange(
                start=LSPPosition(line=def_line, character=0),
                end=LSPPosition(line=def_line, character=100)
            )
        )

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': location.to_dict()
        }

    def _handle_references(self, request_id: Optional[int], params: Dict) -> Dict:
        """Handle textDocument/references request"""
        uri = params['textDocument']['uri']
        position = LSPPosition.from_dict(params['position'])

        if uri not in self.models:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': []
            }

        model = self.models[uri]
        parser = JovialSemanticParser()
        parser.model = model
        parser.lines = self.documents[uri].split('\n')

        hover_info = parser.get_hover_info(position.line, position.character)

        if not hover_info:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': []
            }

        # Find all references
        references = []
        symbol_name = hover_info.get('name', '')

        if symbol_name:
            text = self.documents[uri]
            lines = text.split('\n')

            import re
            pattern = re.compile(r'\b' + re.escape(symbol_name) + r'\b', re.IGNORECASE)

            for i, line in enumerate(lines):
                for match in pattern.finditer(line):
                    ref_range = LSPRange(
                        start=LSPPosition(line=i, character=match.start()),
                        end=LSPPosition(line=i, character=match.end())
                    )
                    references.append(LSPLocation(uri=uri, range=ref_range).to_dict())

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': references
        }

    def _handle_document_symbol(self, request_id: Optional[int], params: Dict) -> Dict:
        """Handle textDocument/documentSymbol request"""
        uri = params['textDocument']['uri']

        if uri not in self.models:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': []
            }

        model = self.models[uri]
        symbols = []

        # Symbol kinds:
        # 5 = Class, 6 = Method/Function, 13 = Variable, 14 = Constant

        # Add items (top-level only)
        seen_items = set()
        for name, item in model.items.items():
            if '.' in name or name in seen_items:
                continue
            seen_items.add(name)

            kind = 14 if item.is_constant else 13  # Constant or Variable
            symbols.append({
                'name': name,
                'kind': kind,
                'location': {
                    'uri': uri,
                    'range': {
                        'start': {'line': item.line_number, 'character': item.column_start},
                        'end': {'line': item.line_number, 'character': item.column_end}
                    }
                },
                'detail': f'{item.type.value} {item.size or ""}'.strip()
            })

        # Add tables
        for name, table in model.tables.items():
            dims = ', '.join([f"{d[0]}:{d[1]}" for d in table.dimensions])
            symbols.append({
                'name': name,
                'kind': 5,  # Class
                'location': {
                    'uri': uri,
                    'range': {
                        'start': {'line': table.line_start, 'character': 0},
                        'end': {'line': table.line_end or table.line_start, 'character': 100}
                    }
                },
                'detail': f'TABLE ({dims})'
            })

        # Add procs
        for name, proc in model.procs.items():
            params_str = ', '.join([p[0] for p in proc.parameters])
            symbols.append({
                'name': name,
                'kind': 6,  # Method/Function
                'location': {
                    'uri': uri,
                    'range': {
                        'start': {'line': proc.line_start, 'character': 0},
                        'end': {'line': proc.line_end or proc.line_start, 'character': 100}
                    }
                },
                'detail': f'PROC ({params_str})'
            })

        # Add defines
        for name, define in model.defines.items():
            symbols.append({
                'name': name,
                'kind': 14,  # Constant
                'location': {
                    'uri': uri,
                    'range': {
                        'start': {'line': define.line_number, 'character': 0},
                        'end': {'line': define.line_number, 'character': 100}
                    }
                },
                'detail': f'DEFINE = {define.value}'
            })

        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'result': symbols
        }


def main():
    """Main entry point for LSP server"""
    server = JovialLSPServer()

    while True:
        try:
            # Read header
            header = ""
            while True:
                char = sys.stdin.read(1)
                if not char:
                    return
                header += char
                if header.endswith('\r\n\r\n') or header.endswith('\n\n'):
                    break

            # Parse Content-Length header
            content_length = 0
            for line in header.split('\n'):
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1].strip())
                    break

            # Read message body
            if content_length > 0:
                message = sys.stdin.read(content_length)
                if not message:
                    break

                try:
                    request = json.loads(message)
                    response = server.handle_request(request)

                    if response:
                        response_json = json.dumps(response)
                        response_text = f"Content-Length: {len(response_json)}\r\n\r\n{response_json}"
                        sys.stdout.write(response_text)
                        sys.stdout.flush()

                except json.JSONDecodeError as e:
                    error_response = {
                        'jsonrpc': '2.0',
                        'error': {
                            'code': -32700,
                            'message': f'Parse error: {str(e)}'
                        }
                    }
                    error_json = json.dumps(error_response)
                    response_text = f"Content-Length: {len(error_json)}\r\n\r\n{error_json}"
                    sys.stdout.write(response_text)
                    sys.stdout.flush()

                except Exception as e:
                    error_response = {
                        'jsonrpc': '2.0',
                        'error': {
                            'code': -32603,
                            'message': f'Internal error: {str(e)}'
                        }
                    }
                    error_json = json.dumps(error_response)
                    response_text = f"Content-Length: {len(error_json)}\r\n\r\n{error_json}"
                    sys.stdout.write(response_text)
                    sys.stdout.flush()

        except Exception as e:
            sys.stderr.write(f"Fatal error: {str(e)}\n")
            sys.stderr.flush()
            break


if __name__ == '__main__':
    main()
