from distutils.errors import LibError
import stat
from typing import Dict, Type, NamedTuple, Tuple, Optional, List
from clang.cindex import Index, TranslationUnit, CursorKind, SourceLocation, SourceRange, TokenKind
from pprint import pprint
import re


class SrcRange(NamedTuple):
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    @classmethod
    def form_source_range(cls, src_range: SourceRange):
        return cls(
            src_range.start.line, src_range.start.column,
            src_range.end.line, src_range.end.column
        )

    @classmethod
    def from_str(cls, src_range_str: SourceRange):
        match = re.search("(\d+):(\d+)-(\d+):(\d+)", src_range_str)
        if match:
            return cls(
                start_line=int(match.group(1)), start_col=int(match.group(2)),
                end_line=int(match.group(3)), end_col=int(match.group(4))
            )
        raise ValueError()

    def is_one_line(self) -> bool:
        """
        return true if src range spans only one line
        """
        return self.start_line == self.end_line

    def encapsules(self, other_range) -> bool:
        start_earlier = self.start_line < other_range.start_line or \
                        self.start_line == other_range.start_line and \
                        self.start_col <= other_range.start_col

        ends_later = self.end_line > other_range.end_line or \
                     self.end_line == other_range.end_line and \
                     self.end_col >= other_range.end_col

        return start_earlier and ends_later

    def to_dict(self) -> Dict[str, int]:
        return {
            'start_line': self.start_line, 'start_col': self.start_col,
            'end_line': self.end_line, 'end_col': self.end_line
        }

    def __str__(self) -> str:
        return f'{self.start_line}:{self.start_col}-{self.end_line}:{self.end_col}'

    def to_line_str(self) -> str:
        return f'{self.start_line}-{self.end_line}'


class CodeAnalysis:
    def __init__(self, ast: TranslationUnit):

        self.range_to_node_type = dict()
        self.func_name_stack = dict()
        self.range_to_idf = dict()
        self.idf_to_range = dict()

        self.lit_to_range = dict()
        self.range_to_lit = dict()

        self.root_cursor = ast.cursor

        self.traverse(self.root_cursor)

        self.token_list, self.token_range_list, self.token_type_list, self.line_to_token_seqence = \
            self.get_token_data(ast.cursor)

        self.scope_to_idf = self.map_scope_to_idf()
        self.scope_to_lit = self.map_scope_to_lit()

    @classmethod
    def from_source(cls, path: str, code: bytes):
        # index = Index.create()
        ast = TranslationUnit.from_source(
            path,
            # args=['-Wall',
            #       '/home/steiner/eth/01_SS22/AST_AutomatedSoftwareTesting/Project/SemSeed/benchmarks/__top_c_repos/proxychains-ng'
            #       ],
            args=['-xcpp-output'],
            unsaved_files=[(path, code)]
        )
        return cls(ast)

    @classmethod
    def from_file(cls, path: str):
        ast = TranslationUnit.from_source(path, args=['-xcpp-output', '-fdirectives-only'])
        return cls(ast)

    @staticmethod
    def is_literal(kind: CursorKind) -> Optional[str]:
        if kind == CursorKind.INTEGER_LITERAL:
            return 'int'
        if kind == CursorKind.FLOATING_LITERAL:
            return 'float'
        if kind == CursorKind.CHARACTER_LITERAL:
            return 'char'
        if kind == CursorKind.STRING_LITERAL:
            return 'string'
        if kind == CursorKind.CXX_BOOL_LITERAL_EXPR:
            return 'bool'

        return None

    def traverse(self, root_cursor) -> None:

        def rec_traverse(node, parent_func_name, parent_func_range) -> None:
            start = node.extent.start
            end = node.extent.end
            src_range = SrcRange(start.line, start.column,
                                 end.line, end.column)

            line = f'{start.line}-{end.line}'

            self.range_to_node_type[src_range] = str(node.kind)

            if node.kind == CursorKind.TRANSLATION_UNIT:
                func_name = f'__GLOBAL_{src_range}'
                self.func_name_stack[func_name] = src_range

                for child in node.get_children():
                    rec_traverse(child, func_name, src_range)
                return

            if node.kind == CursorKind.FUNCTION_DECL:
                func_name = node.spelling
                assert func_name
                self.func_name_stack[f'{func_name}_{src_range}'] = src_range

                for child in node.get_children():
                    rec_traverse(child, func_name, src_range)
                return

            # if node.kind == CursorKind.IF_STMT:

            lit_type = self.is_literal(node.kind)
            if lit_type:
                token_list = list(node.get_tokens())
                # print([t.spelling for t in token_list])
                # assert len(token_list) == 1

                if token_list:
                    lit_value = token_list[0].spelling

                    self.lit_to_range.setdefault(lit_value, []).append({
                        'lit_range': src_range, 'parent_func_range': parent_func_range
                    })
                    self.range_to_lit[src_range] = {
                        'value': lit_value, 'type': lit_type, 'line': line
                    }

            elif node.kind == CursorKind.DECL_REF_EXPR or \
                    node.kind == CursorKind.LABEL_REF or \
                    node.kind == CursorKind.VAR_DECL or \
                    node.kind == CursorKind.PARM_DECL:
                # print(f"{node.kind=} {node.displayname=} {node.spelling=}")
                self.range_to_idf[src_range] = {
                    'name': node.displayname, 'line': line
                }
                self.idf_to_range.setdefault(node.displayname, []).append(
                    {'idf_range': src_range, 'parent_func_range': parent_func_range}
                )

            elif node.kind == CursorKind.UNEXPOSED_EXPR:
                print(f'param: {list(map(lambda x: x.spelling, node.get_tokens()))}')
                for token in node.get_tokens():
                    if token.kind == TokenKind.IDENTIFIER:
                        token_src_range = SrcRange.form_source_range(token.extent)
                        self.range_to_idf[token_src_range] = {
                            'name': token.spelling, 'line': line
                        }
                        self.idf_to_range.setdefault(token.spelling, []).append(
                            {'idf_range': token_src_range, 'parent_func_range': parent_func_range}
                        )
                    elif token.kind == TokenKind.LITERAL:
                        token_src_range = SrcRange.form_source_range(token.extent)
                        lit_value = token.spelling
                        lit_type = str(type(lit_value))
                        self.lit_to_range.setdefault(lit_value, []).append({
                            'lit_range': token_src_range, 'parent_func_range': parent_func_range
                        })
                        self.range_to_lit[token_src_range] = {
                            'value': lit_value, 'type': lit_type, 'line': line
                        }


            else:
                # print(f'{node.kind}: {len(list(node.get_children()))}')

                for child in node.get_children():
                    rec_traverse(child, parent_func_name, parent_func_range)
            return

        rec_traverse(root_cursor, None, None)

    def get_token_data(self, root_cursor
                       ) -> Tuple[List[str], List[SrcRange], List[TokenKind], Dict[int, List[str]]]:
        token_list: List[str] = []  # list of token values
        token_range_list: List[SrcRange] = []  # list of token ranges
        token_type_list: List[TokenKind] = []  # list of token types
        line_to_token_seqence: Dict[int, List[str]] = dict()

        for token in root_cursor.get_tokens():
            src_range = SrcRange.form_source_range(token.extent)

            if src_range in self.range_to_lit:
                token_value = self.range_to_lit[src_range]['value']
            else:
                token_value = token.spelling

            token_list.append(token_value)
            token_type_list.append(token.kind)
            token_range_list.append(src_range)

            if src_range.is_one_line():
                line_to_token_seqence.setdefault(
                    src_range.start_line, []).append(token_value)

        return token_list, token_range_list, token_type_list, line_to_token_seqence

    def map_scope_to_idf(self):
        scope_to_idf = dict()
        for idf, scope_list in self.idf_to_range.items():
            for idf_scope in scope_list:
                parent_func_range = idf_scope['parent_func_range']
                scope_to_idf.setdefault(parent_func_range, set()).add(idf)

        return scope_to_idf

    def map_scope_to_lit(self):
        scope_to_lit = dict()
        for lit, scope_list in self.lit_to_range.items():
            for lit_info in scope_list:
                parent_func_range = lit_info['parent_func_range']
                scope_to_lit.setdefault(parent_func_range, set()).add(lit)

        return scope_to_lit
